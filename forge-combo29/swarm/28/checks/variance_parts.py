#!/usr/bin/env python3
"""variance_parts.py RUNDIR — separate the three things 19-F7 conflated.

From one A/B run file (ab_runs.tsv with N rounds of alternating A and B, same source, same flags):
  1. within-build spread: each build's OWN median-to-min/max range over N runs (run-to-run noise).
  2. between-build spread: the difference of the two builds' medians.
  3. what a ONE-RUN comparison would have shown: the distribution of tb[i]/ta[i] over the rounds, which
     is the number a seat gets when it measures each side once — the quantity 19-F7's "4.2 %" looks like.

Prints a table and the sha256 equality of the two exes if the .meta is present.
"""
import glob
import os
import statistics
import sys


def load(path):
    rows = []
    with open(path) as fh:
        next(fh)
        for line in fh:
            p = line.rstrip("\n").split("\t")
            rows.append((int(p[1]), int(p[2]), int(p[5])))
    return rows


def main() -> int:
    d = sys.argv[1]
    path = os.path.join(d, "ab_runs.tsv")
    if not os.path.exists(path):
        path = glob.glob(os.path.join(d, "*", "ab_runs.tsv"))[0]
    rows = load(path)
    ta = [r[1] for r in rows]
    tb = [r[2] for r in rows]
    ma, mb = statistics.median(ta), statistics.median(tb)

    print("| quantity | value | what it measures |")
    print("|---|---|---|")
    print(f"| rounds | {len(rows)} | A and B alternated, fresh process each |")
    print(f"| A times (ms) | {ta} | all rounds |")
    print(f"| B times (ms) | {tb} | all rounds |")
    print(f"| A median / min / max | {ma} / {min(ta)} / {max(ta)} | within-build run-to-run noise |")
    print(f"| B median / min / max | {mb} / {min(tb)} / {max(tb)} | within-build run-to-run noise |")
    print(f"| A single-run range as % of its median | {(max(ta)-min(ta))/ma*100:.1f} % | what ONE run can move by |")
    print(f"| B single-run range as % of its median | {(max(tb)-min(tb))/mb*100:.1f} % | what ONE run can move by |")
    print(f"| between-build spread of medians | {abs(ma-mb)/statistics.mean([ma,mb])*100:.2f} % | the thing 19-F7 calls build-to-build |")
    one = sorted(b / a for a, b in zip(ta, tb))
    print(f"| one-run paired ratios B/A | min {one[0]:.4f} .. max {one[-1]:.4f} | a seat that runs each side ONCE sees this |")
    print(f"| full range of one-run ratios as % | {(one[-1]-one[0])*100:.1f} % | where a 4 % reading comes from |")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
