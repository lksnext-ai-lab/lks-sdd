"""Windows CLI accounting, including descendant CPU and kernel job commit peak."""
import ctypes
from ctypes import wintypes as W
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time
from unittest.mock import patch


class IO(ctypes.Structure):
    _fields_ = [(n,ctypes.c_ulonglong) for n in ('read_ops','write_ops','other_ops','read_bytes','write_bytes','other_bytes')]
class Accounting(ctypes.Structure):
    _fields_ = [(n,ctypes.c_longlong) for n in ('user','kernel','period_user','period_kernel')] + [(n,W.DWORD) for n in ('faults','processes','active','terminated')]
class BasicLimits(ctypes.Structure):
    _fields_ = [('process_time',ctypes.c_longlong),('job_time',ctypes.c_longlong),('flags',W.DWORD),
                ('min_ws',ctypes.c_size_t),('max_ws',ctypes.c_size_t),('active',W.DWORD),('affinity',ctypes.c_size_t),
                ('priority',W.DWORD),('scheduling',W.DWORD)]
class ExtendedLimits(ctypes.Structure):
    _fields_ = [('basic',BasicLimits),('io',IO)] + [(n,ctypes.c_size_t) for n in ('process_limit','job_limit','process_peak_commit','job_peak_commit')]
class Memory(ctypes.Structure):
    _fields_ = [('size',W.DWORD),('faults',W.DWORD)] + [(n,ctypes.c_size_t) for n in ('peak_ws','ws','peak_page_pool','page_pool','peak_nonpage_pool','nonpage_pool','pagefile','peak_pagefile')]


def resume_owned_child(kernel, tid):
    # Popen closes the initial thread handle. Reopen only the primary thread of
    # this newly created suspended child, after assigning its accounting job.
    kernel.OpenThread.argtypes = [W.DWORD,W.BOOL,W.DWORD]; kernel.OpenThread.restype = W.HANDLE
    kernel.ResumeThread.argtypes = [W.HANDLE]; kernel.ResumeThread.restype = W.DWORD
    handle = kernel.OpenThread(2,False,tid)
    if not handle: raise ctypes.WinError(ctypes.get_last_error())
    try:
        previous = kernel.ResumeThread(handle)
        if previous == 0xFFFFFFFF: raise ctypes.WinError(ctypes.get_last_error())
        if previous != 1: raise RuntimeError('Unexpected primary-thread suspension count')
    finally: kernel.CloseHandle(handle)


def run(arguments, cwd, invocation, timeout=600):
    if sys.platform != 'win32': raise RuntimeError('Windows CLI accounting required')
    kernel = ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.CreateJobObjectW.argtypes = [ctypes.c_void_p,W.LPCWSTR]; kernel.CreateJobObjectW.restype = W.HANDLE
    kernel.SetInformationJobObject.argtypes = [W.HANDLE,ctypes.c_int,ctypes.c_void_p,W.DWORD]
    kernel.QueryInformationJobObject.argtypes = [W.HANDLE,ctypes.c_int,ctypes.c_void_p,W.DWORD,ctypes.c_void_p]
    kernel.AssignProcessToJobObject.argtypes = [W.HANDLE,W.HANDLE]
    kernel.GetProcessTimes.argtypes = [W.HANDLE,*([ctypes.POINTER(W.FILETIME)]*4)]
    kernel.CloseHandle.argtypes = [W.HANDLE]
    psapi = ctypes.WinDLL('psapi',use_last_error=True)
    psapi.GetProcessMemoryInfo.argtypes = [W.HANDLE,ctypes.c_void_p,W.DWORD]
    job = kernel.CreateJobObjectW(None,None)
    if not job: raise ctypes.WinError(ctypes.get_last_error())
    child = None; stopped = threading.Event(); readings = []
    try:
        limits = ExtendedLimits(); limits.basic.flags = 0x2000  # only this owned process tree
        if not kernel.SetInformationJobObject(job,9,ctypes.byref(limits),ctypes.sizeof(limits)):
            raise ctypes.WinError(ctypes.get_last_error())
        script_at = next(i for i,a in enumerate(arguments) if a.endswith('/scripts/lks_sdd.py') or a.endswith('\\scripts\\lks_sdd.py'))
        command = [*arguments[:script_at],str(Path(__file__).with_name('approval_command_worker.py')),*arguments[script_at:]]
        started = time.perf_counter()
        import _winapi
        created_threads = []
        create_process = _winapi.CreateProcess
        def capture_primary_thread(*args, **kwargs):
            result = create_process(*args, **kwargs)
            created_threads.append(result[3])
            return result
        # Observe the actual CreateProcess return, without altering it. This is
        # confined to the harness; the CLI and all its descendants are untouched.
        with patch.object(_winapi,'CreateProcess',capture_primary_thread):
            child = subprocess.Popen(command,cwd=cwd,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                                     env={**os.environ,'PYTHONHASHSEED':'0','LKS_PERFORMANCE_INVOCATION':invocation},creationflags=4)
        if len(created_threads) != 1: raise RuntimeError('Missing owned primary thread identity')
        if not kernel.AssignProcessToJobObject(job,int(child._handle)):
            child.kill(); child.wait(); raise ctypes.WinError(ctypes.get_last_error())
        def observe():
            value = Memory(); value.size = ctypes.sizeof(value)
            if psapi.GetProcessMemoryInfo(int(child._handle),ctypes.byref(value),value.size):
                readings.append((value.ws,value.peak_ws))
        def sample():
            while not stopped.wait(0.01): observe()
        sampler = threading.Thread(target=sample,daemon=True); sampler.start()
        try:
            resume_owned_child(kernel,created_threads[0])
            stdout,stderr = child.communicate(b'run\n',timeout=timeout)
        finally:
            stopped.set(); sampler.join()
        elapsed = time.perf_counter()-started
        created,exited,system,user = [W.FILETIME() for _ in range(4)]
        if not kernel.GetProcessTimes(int(child._handle),*map(ctypes.byref,(created,exited,system,user))):
            raise ctypes.WinError(ctypes.get_last_error())
        seconds = lambda value: ((value.dwHighDateTime<<32)|value.dwLowDateTime)/10000000
        accounting = Accounting()
        if not kernel.QueryInformationJobObject(job,1,ctypes.byref(accounting),ctypes.sizeof(accounting),None):
            raise ctypes.WinError(ctypes.get_last_error())
        if accounting.active:
            raise RuntimeError('CLI exited with active descendants; accounting is incomplete')
        if not kernel.QueryInformationJobObject(job,9,ctypes.byref(limits),ctypes.sizeof(limits),None):
            raise ctypes.WinError(ctypes.get_last_error())
        observe()
        row = {'seconds':elapsed,'cpu_seconds':seconds(system)+seconds(user),
               'job_cpu_seconds':(accounting.user+accounting.kernel)/10000000,'job_processes':accounting.processes,
               'job_active_processes_at_exit':accounting.active,
               'job_peak_commit_bytes':limits.job_peak_commit,'observed_main_peak_working_set_bytes':max((r[1] for r in readings),default=0),
               'sampled_main_working_set_bytes':max((r[0] for r in readings),default=0),'exit_code':child.returncode,
               'job_assigned_before_process_start':True}
        if child.returncode: raise RuntimeError(json.dumps(row)+'\n'+stdout.decode('utf-8')+'\n'+stderr.decode('utf-8'))
        return json.loads(stdout), row
    finally:
        stopped.set()
        kernel.CloseHandle(job)
        if child is not None and child.poll() is None: child.kill(); child.wait()
