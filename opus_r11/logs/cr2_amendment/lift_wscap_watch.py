"""Lift the background-mode working-set cap (hard max 32 MB) of R11 processes started before the CR fix 2 amendment.

CR R3 version. The version that ran on 2026-10-30 12:52-13:15 (log lift_wscap.log) is the one in commit f0d7d364;
Code Review R3 found that it ignored the results of its API calls and re-opened raw PIDs. This version:
- identity: every root PID is resolved ONCE at start into a psutil.Process (pid + create time); it must be running
  and carry --expect in its command line, else the watcher refuses to start and changes nothing. Later passes use
  those objects (is_running() compares pid AND create time, so a reused PID is never taken for a root) and their
  children (psutil skips "children" that are older than their parent, i.e. reused PIDs). A target is changed only
  through a handle opened to it and only when is_running() still holds AFTER the handle was opened (an open handle
  keeps the PID from being reused, so the handle and the checked process are the same);
- scope: only processes with a HARD working-set max (QUOTA_LIMITS_HARDWS_MAX_ENABLE, set by background mode) are
  changed - first memory priority LOW (2), then the normal soft default limits - and the flags are read back.
  Priority class, I/O priority and affinity of the targets are not changed. Nothing is killed;
- fail closed: if this process cannot lower itself (Idle, I/O very low, memory low, affinity), or any call on a
  verified target fails, it logs FAIL and exits without touching anything else.
Usage: lift_wscap_watch.py <log file> --expect <text in each root's command line> [--affinity 0x700] [--once]
                           [--poll 5] <root pid> [<root pid> ...]
Exit: 0 done (all roots ended, or one pass with --once), 1 a call on a verified target failed, 2 refused to start.
"""
import argparse
import ctypes
import sys
import time
from ctypes import wintypes

import psutil

PROCESS_SET_INFORMATION, PROCESS_SET_QUOTA, PROCESS_QUERY_INFORMATION = 0x0200, 0x0100, 0x0400
HARDWS_MIN_DISABLE, HARDWS_MAX_ENABLE, HARDWS_MAX_DISABLE = 0x2, 0x4, 0x8
DEFAULT_MIN, DEFAULT_MAX = 204800, 1413120  # a normal process's soft defaults (50 / 345 pages)
MEMORY_PRIORITY_LOW = 2
PROCESS_MEMORY_PRIORITY = 0  # PROCESS_INFORMATION_CLASS ProcessMemoryPriority

k32 = ctypes.WinDLL("kernel32", use_last_error=True)
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


class Failed(Exception):
    pass


class Watcher:
    def __init__(self, log_path: str):
        self.log_path = log_path
        self.changed = 0

    def log(self, msg: str) -> None:
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(time.strftime("%Y-%m-%dT%H:%M:%S ") + msg + "\n")

    @staticmethod
    def lower_self(mask: int) -> list[str]:
        """Idle class, I/O priority very low, memory priority low, CPU mask; returns what could NOT be set."""
        me = k32.GetCurrentProcess()
        failed = []
        if not k32.SetPriorityClass(me, 0x40):
            failed.append("Idle class")
        try:
            psutil.Process().ionice(psutil.IOPRIO_VERYLOW)
        except (OSError, psutil.Error):
            failed.append("I/O priority very low")
        low = wintypes.ULONG(MEMORY_PRIORITY_LOW)
        if not k32.SetProcessInformation(me, PROCESS_MEMORY_PRIORITY, ctypes.byref(low), 4):
            failed.append("memory priority low")
        if not k32.SetProcessAffinityMask(me, mask):
            failed.append(f"affinity {hex(mask)}")
        return failed

    @staticmethod
    def ws_flags(h) -> tuple[int, int]:
        mn, mx, fl = ctypes.c_size_t(), ctypes.c_size_t(), wintypes.DWORD()
        if not k32.GetProcessWorkingSetSizeEx(h, ctypes.byref(mn), ctypes.byref(mx), ctypes.byref(fl)):
            raise Failed(f"GetProcessWorkingSetSizeEx failed, error {ctypes.get_last_error()}")
        return mx.value, fl.value

    def lift(self, p: psutil.Process) -> None:
        h = k32.OpenProcess(PROCESS_SET_INFORMATION | PROCESS_SET_QUOTA | PROCESS_QUERY_INFORMATION, False, p.pid)
        if not h:
            if not p.is_running():
                return  # it ended (or its PID now names another process): nothing to do
            raise Failed(f"OpenProcess({p.pid}) failed for a running target, error {ctypes.get_last_error()}")
        try:
            if not p.is_running():
                return  # the handle may name a new process that reuses the PID: never touch it
            mx, fl = self.ws_flags(h)
            if not fl & HARDWS_MAX_ENABLE:
                return
            # everything the log needs is read BEFORE the change (a target that ends now changes nothing)
            name, created, cmd, wset = p.name(), p.create_time(), " ".join(p.cmdline())[:160], p.memory_info().wset
            low = wintypes.ULONG(MEMORY_PRIORITY_LOW)
            if not k32.SetProcessInformation(h, PROCESS_MEMORY_PRIORITY, ctypes.byref(low), 4):
                raise Failed(f"pid {p.pid}: memory priority low failed, error {ctypes.get_last_error()}; cap kept")
            if not k32.SetProcessWorkingSetSizeEx(h, DEFAULT_MIN, DEFAULT_MAX, HARDWS_MIN_DISABLE | HARDWS_MAX_DISABLE):
                raise Failed(f"pid {p.pid}: SetProcessWorkingSetSizeEx failed, error {ctypes.get_last_error()}; "
                             "memory priority is low, cap kept")
            mx2, fl2 = self.ws_flags(h)
            if fl2 & HARDWS_MAX_ENABLE:
                raise Failed(f"pid {p.pid}: read-back still shows a hard max (flags {fl2:#x})")
            self.changed += 1
            self.log(f"pid {p.pid} {name} created {created:.3f}: hard max {mx // 2**20} MB flags {fl:#x} "
                     f"wset {wset // 2**20} MB -> memory priority low, soft defaults (flags {fl2:#x}); cmd {cmd}")
        finally:
            k32.CloseHandle(h)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("log")
    ap.add_argument("--expect", required=True, help="text every root's command line must contain")
    ap.add_argument("--affinity", default="0x700")
    ap.add_argument("--once", action="store_true", help="one pass, then exit")
    ap.add_argument("--poll", type=float, default=5.0)
    ap.add_argument("roots", nargs="+", type=int)
    a = ap.parse_args(argv)
    w = Watcher(a.log)
    mask = int(a.affinity, 0)
    if bin(mask).count("1") > 3 or mask <= 0:
        w.log(f"FAIL --affinity {a.affinity} must select 1..3 CPUs; nothing changed")
        return 2
    failed = w.lower_self(mask)
    if failed:
        w.log(f"FAIL could not lower this process ({', '.join(failed)}); nothing changed")
        return 2
    roots = []
    for pid in a.roots:
        try:
            p = psutil.Process(pid)
            cmd = " ".join(p.cmdline())
            created = p.create_time()
        except psutil.Error as e:
            w.log(f"FAIL root {pid}: {type(e).__name__}; nothing changed")
            return 2
        if a.expect not in cmd:
            w.log(f"FAIL root {pid} does not carry {a.expect!r} in its command line ({cmd[:120]}); nothing changed")
            return 2
        roots.append(p)
        w.log(f"root {pid} created {created:.3f}: {cmd[:160]}")
    while True:
        alive = [r for r in roots if r.is_running()]
        if not alive:
            break
        for r in alive:
            try:
                procs = [r] + r.children(recursive=True)
            except psutil.NoSuchProcess:
                continue
            for p in procs:
                try:
                    w.lift(p)
                except psutil.NoSuchProcess:
                    continue
                except (Failed, psutil.Error) as e:
                    w.log(f"FAIL {e}; stopping, nothing else is changed")
                    return 1
        if a.once:
            break
        time.sleep(a.poll)
    w.log(f"done: {w.changed} process(es) changed")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
