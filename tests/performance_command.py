"""Windows CLI accounting, including descendant CPU and kernel job commit peak."""
import ctypes
from ctypes import wintypes as W
import json
import os
from pathlib import Path
import struct
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


def constrain_owned_worker():
    """V401-01's worker-only 512 MiB commit guard, without runtime imports."""
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.CreateJobObjectW.argtypes = [ctypes.c_void_p, W.LPCWSTR]
    kernel.CreateJobObjectW.restype = W.HANDLE
    kernel.SetInformationJobObject.argtypes = [W.HANDLE, ctypes.c_int, ctypes.c_void_p, W.DWORD]
    kernel.AssignProcessToJobObject.argtypes = [W.HANDLE, W.HANDLE]
    kernel.GetCurrentProcess.restype = W.HANDLE
    kernel.CloseHandle.argtypes = [W.HANDLE]
    handle = kernel.CreateJobObjectW(None, None)
    if not handle:
        raise ctypes.WinError(ctypes.get_last_error())
    limits = ExtendedLimits()
    limits.basic.flags = 0x100  # JOB_OBJECT_LIMIT_PROCESS_MEMORY; this worker only
    limits.process_limit = 512 * 1024 * 1024
    if not kernel.SetInformationJobObject(handle, 9, ctypes.byref(limits), ctypes.sizeof(limits)):
        kernel.CloseHandle(handle)
        raise ctypes.WinError(ctypes.get_last_error())
    if not kernel.AssignProcessToJobObject(handle, kernel.GetCurrentProcess()):
        kernel.CloseHandle(handle)
        raise ctypes.WinError(ctypes.get_last_error())
    return kernel, handle


class PowerThrottling(ctypes.Structure):
    _fields_=[('version',W.ULONG),('control',W.ULONG),('state',W.ULONG)]


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


def available_affinity():
    """Observe this process's permitted CPUs; never change OS scheduling policy."""
    if sys.platform!='win32':raise RuntimeError('Windows affinity observation required')
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.GetCurrentProcess.restype=W.HANDLE
    kernel.GetProcessAffinityMask.argtypes=[W.HANDLE,ctypes.POINTER(ctypes.c_size_t),ctypes.POINTER(ctypes.c_size_t)]
    permitted,system=ctypes.c_size_t(),ctypes.c_size_t()
    if not kernel.GetProcessAffinityMask(kernel.GetCurrentProcess(),ctypes.byref(permitted),ctypes.byref(system)):
        raise ctypes.WinError(ctypes.get_last_error())
    return permitted.value


def cpu_topology():
    """Read native CPU-set classes; never infer core type from CPU numbering."""
    if sys.platform!='win32':raise RuntimeError('Windows CPU-set observation required')
    kernel=ctypes.WinDLL('kernel32',use_last_error=True)
    kernel.GetActiveProcessorGroupCount.restype=W.WORD
    if kernel.GetActiveProcessorGroupCount()!=1:
        raise RuntimeError('Measurement requires an explicit single-group policy')
    kernel.GetCurrentProcess.restype=W.HANDLE
    kernel.GetSystemCpuSetInformation.argtypes=[ctypes.c_void_p,W.ULONG,ctypes.POINTER(W.ULONG),W.HANDLE,W.ULONG]
    length=W.ULONG();process=kernel.GetCurrentProcess()
    kernel.GetSystemCpuSetInformation(None,0,ctypes.byref(length),process,0)
    if not 0<length.value<=1048576:raise RuntimeError('Missing or oversized CPU-set information')
    buffer=ctypes.create_string_buffer(length.value)
    if not kernel.GetSystemCpuSetInformation(buffer,len(buffer),ctypes.byref(length),process,0):
        raise ctypes.WinError(ctypes.get_last_error())
    raw=buffer.raw[:length.value];offset=0;rows=[]
    while offset<len(raw):
        if len(raw)-offset<8:raise RuntimeError('Truncated CPU-set information')
        size,kind=struct.unpack_from('<II',raw,offset)
        if size<8 or offset+size>len(raw):raise RuntimeError('Invalid CPU-set record size')
        if kind==0:
            if size<20:raise RuntimeError('Truncated CPU-set record')
            identifier,group,logical,core,cache,numa,efficiency,flags=struct.unpack_from('<IHBBBBBB',raw,offset+8)
            rows.append(dict(id=identifier,group=group,logical=logical,core=core,
                             efficiency_class=efficiency,flags=flags))
        offset+=size
    return rows


def measurement_affinity(rows, allowed):
    """Deterministic highest-performance, unparked, available physical core.

    Choose before timing; no search over benchmark outcomes. For equal classes
    use the last physical core and its first permitted logical CPU, avoiding an
    arbitrary highest bit (which can be an efficiency core on hybrid machines).
    """
    eligible=[r for r in rows if r['group']==0 and allowed&(1<<r['logical']) and
              not r['flags']&1 and (not r['flags']&2 or r['flags']&4)]
    if not eligible:raise RuntimeError('No observed unparked CPU available for measurement')
    fastest=max(r['efficiency_class'] for r in eligible)
    eligible=[r for r in eligible if r['efficiency_class']==fastest]
    core=max(r['core'] for r in eligible)
    return 1<<min(r['logical'] for r in eligible if r['core']==core)


def run(arguments, cwd, invocation, timeout=600, *, affinity_mask=None, performance_mode=False, direct_worker=False):
    if sys.platform != 'win32': raise RuntimeError('Windows CLI accounting required')
    if type(performance_mode) is not bool:raise ValueError('Invalid owned-job performance policy')
    if type(direct_worker) is not bool:raise ValueError('Invalid worker handshake policy')
    if affinity_mask is not None and (type(affinity_mask) is not int or affinity_mask<=0 or
            affinity_mask & (affinity_mask-1) or affinity_mask & ~available_affinity()):
        raise ValueError('Select exactly one CPU allowed to the measurement process')
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
        if affinity_mask is not None:
            limits.basic.flags |= 0x10  # JOB_OBJECT_LIMIT_AFFINITY; owned descendants only
            limits.basic.affinity=affinity_mask
        if performance_mode:
            limits.basic.flags |= 0x20  # JOB_OBJECT_LIMIT_PRIORITY_CLASS, owned tree only
            limits.basic.priority=0x8000  # ABOVE_NORMAL, never high or realtime
        if not kernel.SetInformationJobObject(job,9,ctypes.byref(limits),ctypes.sizeof(limits)):
            raise ctypes.WinError(ctypes.get_last_error())
        if direct_worker:
            # A coordinator supplies its own stdin handshake and runtime choice;
            # do not inject the approval benchmark's clock or UUID generation.
            command = list(arguments)
        else:
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
        power=None
        if performance_mode:
            # Explicit HighQoS for this suspended measurement worker only. This
            # avoids foreground/background QoS inference, not machine power plans.
            kernel.SetProcessInformation.argtypes=kernel.GetProcessInformation.argtypes=[W.HANDLE,ctypes.c_int,ctypes.c_void_p,W.DWORD]
            power=PowerThrottling(1,1,0)
            if not kernel.SetProcessInformation(int(child._handle),4,ctypes.byref(power),ctypes.sizeof(power)):
                raise ctypes.WinError(ctypes.get_last_error())
            if not kernel.GetProcessInformation(int(child._handle),4,ctypes.byref(power),ctypes.sizeof(power)):
                raise ctypes.WinError(ctypes.get_last_error())
            if power.control&1!=1 or power.state&1:
                raise RuntimeError('Owned measurement worker did not retain explicit HighQoS')
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
        if affinity_mask is not None and (not limits.basic.flags & 0x10 or limits.basic.affinity!=affinity_mask):
            raise RuntimeError('Owned job did not retain its declared CPU affinity')
        if performance_mode and (not limits.basic.flags&0x20 or limits.basic.priority!=0x8000):
            raise RuntimeError('Owned measurement job did not retain its declared priority')
        observe()
        row = {'seconds':elapsed,'cpu_seconds':seconds(system)+seconds(user),
               'job_cpu_seconds':(accounting.user+accounting.kernel)/10000000,'job_processes':accounting.processes,
               'job_active_processes_at_exit':accounting.active,
               'job_peak_commit_bytes':limits.job_peak_commit,'observed_main_peak_working_set_bytes':max((r[1] for r in readings),default=0),
               'sampled_main_working_set_bytes':max((r[0] for r in readings),default=0),'exit_code':child.returncode,
               'job_assigned_before_process_start':True,'job_affinity_mask':affinity_mask,
               'owned_job_performance_mode':performance_mode,
               'owned_job_priority':limits.basic.priority if performance_mode else None,
               'worker_power_throttling':{'control':power.control,'state':power.state} if power else None}
        if child.returncode: raise RuntimeError(json.dumps(row)+'\n'+stdout.decode('utf-8')+'\n'+stderr.decode('utf-8'))
        return json.loads(stdout), row
    finally:
        stopped.set()
        kernel.CloseHandle(job)
        if child is not None and child.poll() is None: child.kill(); child.wait()
