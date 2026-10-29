"""R6 guard: run a Python script in-process under a free-RAM watchdog.

usage: python guard_exec.py SCRIPT [ARGS...]
  R6_MIN_FREE_GB (default 7.0): this job aborts itself (os._exit(97)) as soon as
  free physical RAM drops below it; it also refuses to start below floor + 1 GB.
  R6_GUARD_LOG: optional path for a one-line JSON summary (min free RAM, own peak).
  R6_EPOCH_TIMER=1: when SCRIPT is nnue-pytorch's train.py, print positions/s per
  epoch from epoch-end timestamps (needs R6_EPOCH_SIZE = --epoch-size).
The job is one process (data-loader threads included), so aborting it frees all
of its memory at once.  Written after the 2026-10-29 14:29 incident (the live
trainer died at the commit limit while a bigger benchmark ran).
"""

import ctypes
import json
import os
import runpy
import sys
import threading
import time

MIN_GB = float(os.environ.get("R6_MIN_FREE_GB", "7.0"))
POLL_S = 0.25


class _MemStat(ctypes.Structure):
    _fields_ = [
        ("dwLength", ctypes.c_ulong),
        ("dwMemoryLoad", ctypes.c_ulong),
        ("ullTotalPhys", ctypes.c_ulonglong),
        ("ullAvailPhys", ctypes.c_ulonglong),
        ("ullTotalPageFile", ctypes.c_ulonglong),
        ("ullAvailPageFile", ctypes.c_ulonglong),
        ("ullTotalVirtual", ctypes.c_ulonglong),
        ("ullAvailVirtual", ctypes.c_ulonglong),
        ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
    ]


class _ProcMem(ctypes.Structure):
    _fields_ = [
        ("cb", ctypes.c_ulong),
        ("PageFaultCount", ctypes.c_ulong),
        ("PeakWorkingSetSize", ctypes.c_size_t),
        ("WorkingSetSize", ctypes.c_size_t),
        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
        ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
        ("PagefileUsage", ctypes.c_size_t),
        ("PeakPagefileUsage", ctypes.c_size_t),
        ("PrivateUsage", ctypes.c_size_t),
    ]


_k32 = ctypes.windll.kernel32
_k32.GetCurrentProcess.restype = ctypes.c_void_p


def free_gb() -> float:
    st = _MemStat()
    st.dwLength = ctypes.sizeof(_MemStat)
    _k32.GlobalMemoryStatusEx(ctypes.byref(st))
    return st.ullAvailPhys / 2**30


def commit_free_gb() -> float:
    st = _MemStat()
    st.dwLength = ctypes.sizeof(_MemStat)
    _k32.GlobalMemoryStatusEx(ctypes.byref(st))
    return st.ullAvailPageFile / 2**30


def own_private_gb() -> float:
    pm = _ProcMem()
    pm.cb = ctypes.sizeof(_ProcMem)
    _k32.K32GetProcessMemoryInfo(ctypes.c_void_p(_k32.GetCurrentProcess()), ctypes.byref(pm), pm.cb)
    return pm.PrivateUsage / 2**30


STATS = {"min_free_gb": 1e9, "min_commit_free_gb": 1e9, "peak_private_gb": 0.0, "aborted": False}
_T0 = time.time()


def _summary(code):
    STATS["exit_code"] = code
    STATS["wall_s"] = round(time.time() - _T0, 1)
    for k in ("min_free_gb", "min_commit_free_gb", "peak_private_gb"):
        STATS[k] = round(STATS[k], 2)
    line = "[guard] " + json.dumps(STATS)
    print(line, flush=True)
    path = os.environ.get("R6_GUARD_LOG")
    if path:
        with open(path, "a", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps({"script": sys.argv[1:3], **STATS}) + "\n")


def _watch():
    global MIN_GB
    test_floor = os.environ.get("R6_GUARD_SELFTEST_FLOOR")  # self-test of the abort path only
    if test_floor:
        MIN_GB = float(test_floor)
    while True:
        f = free_gb()
        c = commit_free_gb()
        p = own_private_gb()
        STATS["min_free_gb"] = min(STATS["min_free_gb"], f)
        STATS["min_commit_free_gb"] = min(STATS["min_commit_free_gb"], c)
        STATS["peak_private_gb"] = max(STATS["peak_private_gb"], p)
        if f < MIN_GB:
            STATS["aborted"] = True
            print(f"[guard] ABORT own job: free RAM {f:.2f} GB < {MIN_GB} GB (own private {p:.2f} GB)", flush=True)
            _summary(97)
            _real_exit(97)
        time.sleep(POLL_S)


_real_exit = os._exit


def _exit_hook(code):
    _summary(code)
    sys.stdout.flush()
    _real_exit(code)


def _install_epoch_timer():
    size = int(os.environ["R6_EPOCH_SIZE"])
    import trainer.engine as E

    orig = E.SimpleTrainer._train_epoch
    marks = []

    def timed_epoch(self, loader):
        r = orig(self, loader)  # ends with .item() on the epoch loss -> GPU synced
        marks.append(time.perf_counter())
        if len(marks) >= 2:
            dt = marks[-1] - marks[-2]
            STATS.setdefault("pos_per_s", []).append(round(size / dt))
            print(f"[guard] epoch {len(marks) - 1}: {size / dt:,.0f} pos/s, free RAM {free_gb():.1f} GB, "
                  f"own private {own_private_gb():.2f} GB", flush=True)
        return r

    E.SimpleTrainer._train_epoch = timed_epoch


def main():
    script = sys.argv[1]
    f = free_gb()
    if f < MIN_GB + 1.0:
        print(f"[guard] not starting: free RAM {f:.2f} GB < {MIN_GB + 1.0} GB", flush=True)
        _real_exit(3)
    print(f"[guard] start: free RAM {f:.2f} GB, floor {MIN_GB} GB, script {script}", flush=True)
    threading.Thread(target=_watch, daemon=True).start()
    os._exit = _exit_hook
    sys.argv = [script, *sys.argv[2:]]
    sys.path.insert(0, os.path.dirname(os.path.abspath(script)))
    if os.environ.get("R6_EPOCH_TIMER") == "1":
        sys.path.insert(0, os.getcwd())
        _install_epoch_timer()
    code = 0
    try:
        runpy.run_path(script, run_name="__main__")
    except SystemExit as e:
        code = e.code if isinstance(e.code, int) else (0 if e.code is None else 1)
    except BaseException:
        import traceback

        traceback.print_exc()
        code = 1
    _summary(code)
    sys.stdout.flush()
    _real_exit(code)


if __name__ == "__main__":
    main()
