#!/usr/bin/env python3
"""prediction_check_19f7.py — score checks/prediction_19f7.txt against out_ab19f7 and rebuild19f7."""
import statistics
import sys


def load(path):
    rows = []
    with open(path) as fh:
        next(fh)
        for line in fh:
            p = line.rstrip("\n").split("\t")
            rows.append((int(p[2]), int(p[5])))
    return rows


def main() -> int:
    path = sys.argv[1]
    rows = load(path)
    ta = [r[0] for r in rows]
    tb = [r[1] for r in rows]
    ma, mb = statistics.median(ta), statistics.median(tb)
    ratio = mb / ma
    spread = abs(ma - mb) / statistics.mean([ma, mb]) * 100
    rows_out = [
        ("P1", "baseA median bench-13", round(ma, 1), 430, 380, 500, "ms"),
        ("P2", "baseB median bench-13", round(mb, 1), 430, 380, 500, "ms"),
        ("P3", "median ratio A/B", round(ratio, 4), 1.00, 0.96, 1.04, "f"),
        ("P5", "spread |A-B|/mean", round(spread, 2), 1.5, 0.0, 8.0, "%"),
    ]
    print("| id | measurement | predicted | measured | kill range | verdict |")
    print("|---|---|---|---|---|---|")
    for pid, name, got, pred, lo, hi, unit in rows_out:
        ok = lo <= float(got) <= hi
        print(f"| {pid} | {name} | {pred} {unit} | {got} {unit} | {lo}..{hi} | "
              f"{'SURVIVES' if ok else '**KILLED**'} |")
    # P4 needs the bootstrap interval from ab_summary.txt
    lo_ci = hi_ci = None
    try:
        for line in open(path.replace("ab_runs.tsv", "ab_summary.txt")):
            if line.startswith("boot95"):
                lo_ci, hi_ci = (float(x) for x in line.split("[")[1].rstrip("]\n").split(","))
    except FileNotFoundError:
        pass
    if lo_ci is not None:
        contains = lo_ci <= 1.0 <= hi_ci
        print(f"| P4 | 95 % CI of the ratio contains 1.0 | true | [{lo_ci:.4f}, {hi_ci:.4f}] | true | "
              f"{'SURVIVES' if contains else '**KILLED**'} |")
    p7 = spread > 4.0
    print(f"| P7 | 19-F7's 4.2 % reproduces here | no | spread {spread:.2f} % | no | "
          f"{'**KILLED**' if p7 else 'SURVIVES'} |")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
