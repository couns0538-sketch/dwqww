#!/usr/bin/env python3
"""R3-6: system-wide CPU busy fraction (GetSystemTimes) over N windows of S seconds, and free RAM.
usage: sysload.py [--windows 6] [--seconds 5]"""
import argparse
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from smp_ttd import free_ram_gb, system_times  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--windows", type=int, default=6)
    ap.add_argument("--seconds", type=float, default=5.0)
    a = ap.parse_args()
    vals = []
    for _ in range(a.windows):
        s0 = system_times()
        time.sleep(a.seconds)
        s1 = system_times()
        idle = s1[0] - s0[0]
        total = (s1[1] - s0[1]) + (s1[2] - s0[2])
        busy = (total - idle) / total
        vals.append(busy)
        print(f"{time.strftime('%H:%M:%S')} busy {busy:.3f} ({busy * os.cpu_count():.1f} of {os.cpu_count()} "
              f"logical CPUs) free RAM {free_ram_gb():.1f} GB", flush=True)
    print(f"mean busy {sum(vals) / len(vals):.3f}")


if __name__ == "__main__":
    main()
