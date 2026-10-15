"""Read-only runner audit. Fresh native identities avoid repeated slow WMI scans."""
import ctypes
from ctypes import wintypes
import hashlib
import json
import os
import subprocess
import sys
import threading

def processes(*, with_parents=False):
    """Toolhelp snapshot plus creation time; a reused PID is a new identity."""
    class Entry(ctypes.Structure):
        _fields_ = [('size',wintypes.DWORD),('usage',wintypes.DWORD),('pid',wintypes.DWORD),
                    ('heap',ctypes.c_size_t),('module',wintypes.DWORD),('threads',wintypes.DWORD),
                    ('parent',wintypes.DWORD),('priority',wintypes.LONG),('flags',wintypes.DWORD),
                    ('exe',wintypes.WCHAR*260)]
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD,wintypes.DWORD]
    kernel.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
    kernel.Process32FirstW.argtypes = kernel.Process32NextW.argtypes = [wintypes.HANDLE,ctypes.POINTER(Entry)]
    kernel.OpenProcess.argtypes = [wintypes.DWORD,wintypes.BOOL,wintypes.DWORD]
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.GetProcessTimes.argtypes = [wintypes.HANDLE,*([ctypes.POINTER(wintypes.FILETIME)]*4)]
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    snapshot = kernel.CreateToolhelp32Snapshot(2,0)
    if snapshot == ctypes.c_void_p(-1).value: raise ctypes.WinError(ctypes.get_last_error())
    result, parents = {}, {}
    try:
        entry = Entry(); entry.size = ctypes.sizeof(entry)
        active = kernel.Process32FirstW(snapshot,ctypes.byref(entry))
        while active:
            parents[int(entry.pid)] = int(entry.parent)
            executable = entry.exe.casefold()
            if executable.startswith('python') and executable.endswith('.exe') and entry.pid != os.getpid():
                handle = kernel.OpenProcess(0x1000,False,entry.pid)
                if handle:
                    try:
                        created,exited,system,user = [wintypes.FILETIME() for _ in range(4)]
                        if not kernel.GetProcessTimes(handle,*map(ctypes.byref,(created,exited,system,user))):
                            raise ctypes.WinError(ctypes.get_last_error())
                        if not (exited.dwHighDateTime or exited.dwLowDateTime):
                            result[int(entry.pid)] = (created.dwHighDateTime << 32) | created.dwLowDateTime
                    finally: kernel.CloseHandle(handle)
                elif ctypes.get_last_error() != 87: raise ctypes.WinError(ctypes.get_last_error())
            active = kernel.Process32NextW(snapshot,ctypes.byref(entry))
    finally: kernel.CloseHandle(snapshot)
    return (result, parents) if with_parents else result


class ConcurrentRunner(RuntimeError):
    pass


class Audit:
    def __init__(self): self.known = {}; self.blocked = {}; self.classifications = []

    def check(self):
        if sys.platform != 'win32': raise RuntimeError('Isolated Windows audit unavailable')
        observed = processes()
        for pid,(created,details) in list(self.blocked.items()):
            if observed.get(pid) == created: raise ConcurrentRunner(json.dumps(details))
            self.blocked.pop(pid)
        unknown = [pid for pid, created in observed.items() if self.known.get(pid) != created]
        if unknown:
            expression = ' OR '.join('ProcessId = ' + str(pid) for pid in unknown)
            script = '[Console]::OutputEncoding = [Text.UTF8Encoding]::new($false); @(Get-CimInstance Win32_Process -Filter "' + expression + '" | Select-Object ProcessId,CommandLine) | ConvertTo-Json -Compress'
            done = subprocess.run(['powershell','-NoProfile','-NonInteractive','-Command',script],capture_output=True,
                                  text=True,encoding='utf-8',check=True,timeout=600)
            rows = json.loads(done.stdout.strip() or '[]')
            if isinstance(rows,dict): rows = [rows]
            fresh = processes()
            for row in rows:
                pid = int(row['ProcessId'])
                if fresh.get(pid) != observed.get(pid): continue
                command = row.get('CommandLine')
                if not isinstance(command,str) or not command: raise RuntimeError('Unknown Python command line: ' + str(pid))
                # No script-name allowlist: an opaque coordinator can launch
                # competing CLI work later. All foreign Python is a conflict.
                details = {'reason':'concurrent-python','pid':pid,'created':observed[pid],
                           'matched_pattern':'any-unowned-python',
                           'command_sha256':hashlib.sha256(command.encode()).hexdigest()}
                self.blocked[pid] = (observed[pid],details)
                raise ConcurrentRunner(json.dumps(details))
            unresolved = [pid for pid, created in fresh.items() if self.known.get(pid) != created]
            if unresolved: raise RuntimeError('Unclassified concurrent Python processes: ' + str(unresolved))
            observed = fresh
        return {'supported':True,'conflicting_pids':[], 'observed_python_identities':observed}


class Watch:
    """Native monitoring only; no WMI queries during measured work.

    A new unowned Python identity invalidates the group, even if it exits before
    the final audit. Owned descendants are recognized through the native tree.
    """
    def __init__(self, audit, child_pid, interval=.5):
        self.allowed = dict(audit.known)
        self.root = child_pid
        self.root_created = processes().get(child_pid)
        if self.root_created is None: raise RuntimeError('Cannot bind owned worker identity')
        self.owned = {child_pid:self.root_created}
        self.unknown = {}; self.errors = []; self.samples = 0
        self.interval = interval; self.done = threading.Event()
        self.thread = threading.Thread(target=self.run,daemon=True)

    def scan(self):
        observed, parents = processes(with_parents=True); self.samples += 1
        for pid,created in observed.items():
            if self.allowed.get(pid) == created or self.owned.get(pid) == created: continue
            ancestor, seen = parents.get(pid), set()
            while ancestor and ancestor not in seen and ancestor != self.root:
                seen.add(ancestor); ancestor = parents.get(ancestor)
            if ancestor == self.root and observed.get(self.root) == self.root_created:
                self.owned[pid] = created
            else:
                self.unknown[(pid,created)] = {'pid':pid,'created':created,'parent':parents.get(pid)}

    def run(self):
        try:
            self.scan()
            while not self.done.wait(self.interval): self.scan()
        except Exception as error: self.errors.append(type(error).__name__+': '+str(error))

    def start(self): self.thread.start()

    def close(self):
        self.done.set(); self.thread.join()
        try: self.scan()
        except Exception as error: self.errors.append(type(error).__name__+': '+str(error))
        return {'interval_seconds':self.interval,'snapshots':self.samples,
                'owned_python_identities':self.owned,'unowned_new_identities':list(self.unknown.values()),'errors':self.errors}
