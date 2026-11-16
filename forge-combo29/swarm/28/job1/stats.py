#!/usr/bin/env python3
"""stats.py OUTDIR run... — median / p99 / largest / over-limit table from timing.py output.

Every number printed here is computed from the .txt files, never typed. `limit` in ms is
movetime, or wtime/30 + winc for the wtime configurations (stated in the header).
"""
import glob
import os
import sys


def limits_for(config):
    if config == "mt50":
        return 50.0, "movetime 50"
    if config == "mt500":
        return 500.0, "movetime 500"
    if config == "wt1000":
        return 1000 / 30 + 10, "wtime/30+winc = 43.3"
    if config == "wt10000":
        return 10000 / 30 + 100, "wtime/30+winc = 433.3"
    raise SystemExit(f"unknown config {config}")


def pct(values, q):
    """Linear-interpolated percentile, q in 0..100."""
    if not values:
        return float("nan")
    s = sorted(values)
    k = (len(s) - 1) * q / 100.0
    lo, hi = int(k), min(int(k) + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (k - lo)


def load(path):
    walls, status = [], []
    with open(path) as fh:
        next(fh)
        for line in fh:
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 6:
                continue
            try:
                walls.append(float(parts[2]))
            except ValueError:
                continue
            status.append(parts[5])
    return walls, status


def main() -> int:
    outdir = sys.argv[1]
    print("| run | searches | ok | median ms | p99 ms | largest ms | limit | over limit | over % |")
    print("|---|---|---|---|---|---|---|---|---|")
    for path in sorted(glob.glob(os.path.join(outdir, "*.txt"))):
        run = os.path.basename(path)[:-4]
        head = run.split("_")[0]
        config = head if head in ("mt50", "mt500", "wt1000", "wt10000") else run
        limit, why = limits_for(config)
        walls, status = load(path)
        ok = sum(1 for s in status if s == "ok")
        over = sum(1 for w in walls if w > limit)
        print(f"| {run} | {len(walls)} | {ok} | {pct(walls,50):.1f} | {pct(walls,99):.1f} | "
              f"{max(walls):.1f} | {why} | {over} | {100.0*over/len(walls):.1f}% |")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
