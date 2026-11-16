#!/usr/bin/env python3
"""harness_overhead.py — wall_ms minus the engine's own reported time, per config.

The difference is the cost of the Go/readyok handshake in this harness (python driver + pipe), not
engine behaviour. Shown so nobody reads the wall numbers as pure engine latency.
"""
import os
import sys


def pct(v, q):
    s = sorted(v)
    k = (len(s) - 1) * q / 100.0
    lo, hi = int(k), min(int(k) + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (k - lo)


def main() -> int:
    d = sys.argv[1]
    print("| config | n with engine time | median delta ms | p99 delta ms | max delta ms |")
    print("|---|---|---|---|---|")
    for name in ["mt50", "mt500", "wt1000", "wt10000"]:
        path = os.path.join(d, "outA", name + ".txt")
        delta = []
        with open(path) as fh:
            next(fh)
            for line in fh:
                p = line.rstrip("\n").split("\t")
                if len(p) >= 6 and p[5] == "ok" and p[4]:
                    delta.append(float(p[2]) - float(p[4]))
        if not delta:
            print(f"| {name} | 0 | - | - | - |")
            continue
        print(f"| {name} | {len(delta)} | {pct(delta,50):.2f} | {pct(delta,99):.2f} | {max(delta):.2f} |")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
