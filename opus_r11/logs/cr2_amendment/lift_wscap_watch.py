"""Lift the background-mode working-set cap (hard max 32 MB) of R11 processes started before the CR fix 2 amendment.

Only the given root PIDs and their descendants are touched, and only when their working-set max is HARD (flag
QUOTA_LIMITS_HARDWS_MAX_ENABLE, which background mode sets): the limits become the normal soft defaults and the memory
priority LOW (2) - the amended R11 setting. Priority class (Idle), I/O priority (very low) and affinity are not changed.
Nothing is killed. Runs at Idle on CPUs 8-10 until every root has exited.
Usage: lift_wscap_watch.py <log file> <root pid> [<root pid> ...]
"""
import ctypes
import sys
import time
from ctypes import wintypes

import psutil

PROCESS_SET_INFORMATION, PROCESS_SET_QUOTA, PROCESS_QUERY_INFORMATION = 0x0200, 0x0100, 0x0400
HARDWS_MIN_DISABLE, HARDWS_MAX_ENABLE, HARDWS_MAX_DISABLE = 0x2, 0x4, 0x8
DEFAULT_MIN, DEFAULT_MAX = 204800, 1413120  # a normal process's soft defaults (50 / 345 pages)

k32 = ctypes.windll.kernel32
k32.GetCurrentProcess.restype = wintypes.HANDLE
k32.OpenProcess.restype = wintypes.HANDLE
k32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
k32.SetProcessInformation.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
k32.SetProcessWorkingSetSizeEx.argtypes = [wintypes.HANDLE, ctypes.c_size_t, ctypes.c_size_t, wintypes.DWORD]
k32.GetProcessWorkingSetSizeEx.argtypes = [wintypes.HANDLE, ctypes.POINTER(ctypes.c_size_t),
                                           ctypes.POINTER(ctypes.c_size_t), ctypes.POINTER(wintypes.DWORD)]
k32.SetPriorityClass.argtypes = [wintypes.HANDLE, wintypes.DWORD]
k32.SetProcessAffinityMask.argtypes = [wintypes.HANDLE, ctypes.c_size_t]
k32.CloseHandle.argtypes = [wintypes.HANDLE]

me = k32.GetCurrentProcess()
k32.SetPriorityClass(me, 0x40)
k32.SetProcessAffinityMask(me, 0x700)
log_path, roots = sys.argv[1], [int(x) for x in sys.argv[2:]]


def log(msg: str) -> None:
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(time.strftime("%Y-%m-%dT%H:%M:%S ") + msg + "\n")


def lift(p: psutil.Process) -> None:
    h = k32.OpenProcess(PROCESS_SET_INFORMATION | PROCESS_SET_QUOTA | PROCESS_QUERY_INFORMATION, False, p.pid)
    if not h:
        return
    try:
        mn, mx, fl = ctypes.c_size_t(), ctypes.c_size_t(), wintypes.DWORD()
        if not k32.GetProcessWorkingSetSizeEx(h, ctypes.byref(mn), ctypes.byref(mx), ctypes.byref(fl)):
            return
        if not fl.value & HARDWS_MAX_ENABLE:
            return
        before = p.memory_info().wset
        ok_ws = k32.SetProcessWorkingSetSizeEx(h, DEFAULT_MIN, DEFAULT_MAX, HARDWS_MIN_DISABLE | HARDWS_MAX_DISABLE)
        low = wintypes.ULONG(2)
        ok_mp = k32.SetProcessInformation(h, 0, ctypes.byref(low), 4)
        log(f"pid {p.pid} {p.name()} hard max {mx.value // 2**20} MB flags {fl.value:#x} wset {before // 2**20} MB -> "
            f"soft defaults ({bool(ok_ws)}), memory priority low ({bool(ok_mp)}); cmd {' '.join(p.cmdline())[:160]}")
    except psutil.Error:
        pass
    finally:
        k32.CloseHandle(h)


log(f"start, roots {roots}")
while True:
    alive = [r for r in roots if psutil.pid_exists(r)]
    if not alive:
        break
    for r in alive:
        try:
            rp = psutil.Process(r)
            for p in [rp] + rp.children(recursive=True):
                lift(p)
        except psutil.Error:
            continue
    time.sleep(5)
log("all roots exited; done")
