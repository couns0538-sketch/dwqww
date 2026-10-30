"""Try to lift the 32 MB working-set cap of a background-mode process from OUTSIDE (no kill, no injection).

Usage: lift_cap.py <pid> memprio|hardws|both
  memprio: SetProcessInformation(ProcessMemoryPriority = MEMORY_PRIORITY_LOW 2)
  hardws:  SetProcessWorkingSetSizeEx(min 64 MB, max 1 GB, HARDWS_MIN_DISABLE | HARDWS_MAX_DISABLE)
Prints what each call returned and the process's working set before/after.
"""
import ctypes
import sys
import time
from ctypes import wintypes

import psutil

PROCESS_SET_INFORMATION = 0x0200
PROCESS_SET_QUOTA = 0x0100
PROCESS_QUERY_INFORMATION = 0x0400
QUOTA_LIMITS_HARDWS_MIN_DISABLE = 0x2
QUOTA_LIMITS_HARDWS_MAX_DISABLE = 0x8

k32 = ctypes.windll.kernel32
k32.OpenProcess.restype = wintypes.HANDLE
k32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
k32.SetProcessInformation.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
k32.GetProcessInformation.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
k32.SetProcessWorkingSetSizeEx.argtypes = [wintypes.HANDLE, ctypes.c_size_t, ctypes.c_size_t, wintypes.DWORD]
k32.GetProcessWorkingSetSizeEx.argtypes = [wintypes.HANDLE, ctypes.POINTER(ctypes.c_size_t),
                                           ctypes.POINTER(ctypes.c_size_t), ctypes.POINTER(wintypes.DWORD)]
k32.CloseHandle.argtypes = [wintypes.HANDLE]

pid, how = int(sys.argv[1]), sys.argv[2]
p = psutil.Process(pid)
h = k32.OpenProcess(PROCESS_SET_INFORMATION | PROCESS_SET_QUOTA | PROCESS_QUERY_INFORMATION, False, pid)
if not h:
    print("OpenProcess failed", ctypes.GetLastError())
    sys.exit(1)


def show(tag: str) -> None:
    mn, mx, fl = ctypes.c_size_t(), ctypes.c_size_t(), wintypes.DWORD()
    k32.GetProcessWorkingSetSizeEx(h, ctypes.byref(mn), ctypes.byref(mx), ctypes.byref(fl))
    mp = wintypes.ULONG(99)
    k32.GetProcessInformation(h, 0, ctypes.byref(mp), 4)
    print(f"{tag}: wset {p.memory_info().wset / 2**20:.0f} MB, ws min {mn.value / 2**20:.1f} MB max "
          f"{mx.value / 2**20:.1f} MB flags {fl.value:#x}, memory priority {mp.value}", flush=True)


show("before")
if how in ("memprio", "both"):
    low = wintypes.ULONG(2)
    ok = k32.SetProcessInformation(h, 0, ctypes.byref(low), 4)
    print("SetProcessInformation(MemoryPriority=2) ->", ok, ctypes.GetLastError())
if how in ("hardws", "both"):
    ok = k32.SetProcessWorkingSetSizeEx(h, 64 * 2**20, 1024 * 2**20,
                                        QUOTA_LIMITS_HARDWS_MIN_DISABLE | QUOTA_LIMITS_HARDWS_MAX_DISABLE)
    print("SetProcessWorkingSetSizeEx(64 MB, 1 GB, soft) ->", ok, ctypes.GetLastError())
for i in range(4):
    time.sleep(1.5)
    show(f"after {1.5 * (i + 1):.1f} s")
k32.CloseHandle(h)
