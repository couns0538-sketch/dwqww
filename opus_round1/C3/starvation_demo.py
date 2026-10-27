#!/usr/bin/env python3
"""Starved-engine latency demo for C3 (the WAC300 harness ran the engine at nice 19, pinned to one core
of a loaded box, and saw a 12 s answer on a 1000 ms move).
Starts a 1-thread CPU hog pinned to logical CPU k (Windows: BELOW_NORMAL priority class; elsewhere
nice 0), then runs tools/latency_test.py on the first N WAC positions with the engine pinned to the
same CPU at the lowest priority (Windows IDLE class / nice 19): once with HardDeadline=0 (lock
behaviour) and once with HardDeadline=G, and stops the hog.
usage: starvation_demo.py <engine> [--cpu 11] [--count 30] [--movetimes 100,1000] [--grace 10] [--out DIR]"""
import argparse
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))


def start_hog(cpu):
    hog = subprocess.Popen([sys.executable, "-c", "while True: pass"])
    if os.name == "nt":
        import ctypes
        k32 = ctypes.windll.kernel32
        handle = int(hog._handle)
        k32.SetProcessAffinityMask(handle, ctypes.c_size_t(1 << cpu))
        k32.SetPriorityClass(handle, 0x4000)  # BELOW_NORMAL_PRIORITY_CLASS
    else:
        os.sched_setaffinity(hog.pid, {cpu})
    return hog


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("engine")
    ap.add_argument("--cpu", type=int, default=11)
    ap.add_argument("--count", type=int, default=30)
    ap.add_argument("--movetimes", default="100,1000")
    ap.add_argument("--grace", type=int, default=10)
    ap.add_argument("--out", default=".")
    a = ap.parse_args()
    hog = start_hog(a.cpu)
    status = 0
    try:
        for grace in (0, a.grace):
            print(f"=== HardDeadline={grace}: engine pinned to CPU {a.cpu} at lowest priority, CPU hog on the same CPU",
                  flush=True)
            cmd = [sys.executable, os.path.join(ROOT, "tools", "latency_test.py"), a.engine,
                   "--suite", os.path.join(ROOT, "tools", "wac300.epd"), "--count", str(a.count), "--movetimes", a.movetimes,
                   "--passes", "1", "--affinity", str(a.cpu), "--idle", "--timeout", "120",
                   "--option", f"HardDeadline={grace}", "--json", os.path.join(a.out, f"starvation_hd{grace}.json")]
            rc = subprocess.call(cmd)
            status |= rc if grace else 0  # the OFF run is expected to fail
    finally:
        hog.kill()
        hog.wait()
    sys.exit(status)


if __name__ == "__main__":
    main()
