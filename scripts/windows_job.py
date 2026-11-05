"""Windows job ownership for the development resource watchdog.

A gated launcher cannot start the command until it belongs to the job. Closing
the job also stops descendants that exit/reparent between psutil samples.
"""

import ctypes
from ctypes import wintypes
import subprocess
import sys
import uuid


class WindowsJob:
    """Own a kill-on-close job and a startup event; instantiated on Windows only."""

    def __init__(self):
        self.kernel = ctypes.WinDLL("kernel32", use_last_error=True)
        self.job = None
        self.event = None
        self.name = "Local\\kerykeion-watchdog-" + uuid.uuid4().hex
        signatures = {
            "CreateJobObjectW": ([ctypes.c_void_p, wintypes.LPCWSTR], wintypes.HANDLE),
            "CreateEventW": ([ctypes.c_void_p, wintypes.BOOL, wintypes.BOOL, wintypes.LPCWSTR], wintypes.HANDLE),
            "SetInformationJobObject": ([wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD], wintypes.BOOL),
            "AssignProcessToJobObject": ([wintypes.HANDLE, wintypes.HANDLE], wintypes.BOOL),
            "OpenProcess": ([wintypes.DWORD, wintypes.BOOL, wintypes.DWORD], wintypes.HANDLE),
            "SetEvent": ([wintypes.HANDLE], wintypes.BOOL),
            "CloseHandle": ([wintypes.HANDLE], wintypes.BOOL),
        }
        for name, (args, result) in signatures.items():
            function = getattr(self.kernel, name)
            function.argtypes, function.restype = args, result

        class BasicLimits(ctypes.Structure):
            _fields_ = [("process_time", ctypes.c_int64), ("job_time", ctypes.c_int64),
                        ("flags", wintypes.DWORD), ("min_working_set", ctypes.c_size_t),
                        ("max_working_set", ctypes.c_size_t), ("active_processes", wintypes.DWORD),
                        ("affinity", ctypes.c_size_t), ("priority", wintypes.DWORD),
                        ("scheduling", wintypes.DWORD)]

        class ExtendedLimits(ctypes.Structure):
            _fields_ = [("basic", BasicLimits), ("io_counters", ctypes.c_uint64 * 6),
                        ("process_memory", ctypes.c_size_t), ("job_memory", ctypes.c_size_t),
                        ("peak_process_memory", ctypes.c_size_t), ("peak_job_memory", ctypes.c_size_t)]

        try:
            self.job = self._check(self.kernel.CreateJobObjectW(None, None))
            limits = ExtendedLimits()
            limits.basic.flags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
            self._check(self.kernel.SetInformationJobObject(self.job, 9, ctypes.byref(limits), ctypes.sizeof(limits)))
            self.event = self._check(self.kernel.CreateEventW(None, True, False, self.name))
        except BaseException:
            self.close()
            raise

    @staticmethod
    def _check(value):
        """Fail closed on any Win32 setup error."""
        if not value:
            raise ctypes.WinError(ctypes.get_last_error())
        return value

    def start(self, command: list[str]) -> subprocess.Popen:
        """Assign the waiting launcher before allowing it to create descendants."""
        launcher = """
import ctypes, subprocess, sys
from ctypes import wintypes
k = ctypes.WinDLL('kernel32', use_last_error=True)
k.OpenEventW.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.LPCWSTR]
k.OpenEventW.restype = wintypes.HANDLE
k.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
k.WaitForSingleObject.restype = wintypes.DWORD
k.CloseHandle.argtypes = [wintypes.HANDLE]
event = k.OpenEventW(0x00100000, False, sys.argv[1])
if not event or k.WaitForSingleObject(event, 30000) != 0:
    raise SystemExit(127)
k.CloseHandle(event)
try:
    code = subprocess.call(sys.argv[2:])
except OSError as exc:
    print(f'Cannot start command: {exc}', file=sys.stderr)
    code = 127
raise SystemExit(code)
"""
        child = subprocess.Popen([sys.executable, "-c", launcher, self.name, *command])
        try:
            process = self._check(self.kernel.OpenProcess(0x0100 | 0x0001, False, child.pid))
            try:
                self._check(self.kernel.AssignProcessToJobObject(self.job, process))
            finally:
                self.kernel.CloseHandle(process)
            self._check(self.kernel.SetEvent(self.event))
        except BaseException:
            child.kill()
            child.wait()
            raise
        return child

    def close(self) -> None:
        """Stop all owned descendants and release the startup event."""
        for attribute in ("job", "event"):
            handle = getattr(self, attribute)
            if handle:
                self.kernel.CloseHandle(handle)
                setattr(self, attribute, None)
