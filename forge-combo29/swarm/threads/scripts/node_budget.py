#!/usr/bin/env python3
"""Does `go nodes N` respect N when helpers are running?

The concern: if each worker treated N as ITS OWN budget, the aggregate would
overshoot by about the thread count. The source says helpers DO carry the budget
(`node_limit_specified_` is true for them because they have no parent_worker_), and
`should_stop_with` compares `total_nodes()` -- a sum over all workers -- against
`node_limit_`. So the prediction is: no overshoot, and the reported total UNDER-shoots
because the budget stops mid-iteration and the reported number is the search's own
running count at that moment.

Two quantities per row, and they are different:
  reported  -- the `nodes` field of the last `info depth` line
  ratio     -- reported / N

An UNDER-shoot is expected and benign (a node budget stops at an iteration
boundary in effect). An OVERSHOOT of about +threads is the defect the brief asks
about. Also reported: whether the search ever reported MORE than N on any line.

Usage: python3 node_budget.py <exe> <fens> <out.json> [reps]
"""
import json
import os
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from engine import Engine, last_depth_info, parse_info  # noqa: E402

THREADS = (1, 2, 4, 8)
BUDGETS = (10000, 100000, 1000000)


def main():
    exe = os.path.abspath(sys.argv[1])
    fens = [l.strip() for l in open(sys.argv[2]) if l.strip()]
    out_path = sys.argv[3]
    reps = int(sys.argv[4]) if len(sys.argv) > 4 else 2
    rows = []
    for th in THREADS:
        e = Engine(exe, {"Hash": 64, "Threads": th}, timeout=600.0)
        for budget in BUDGETS:
            reported, ratios, over = [], [], 0
            for fen in fens:
                for _ in range(reps):
                    e.ucinewgame()
                    e.position(fen)
                    info, best, wall = e.go(f"nodes {budget}", timeout=600.0)
                    d = last_depth_info(info)
                    if d is None:
                        continue
                    reported.append(d["nodes"])
                    ratios.append(d["nodes"] / budget)
                    # every info line's node field, to catch a mid-search overshoot
                    for line in info:
                        p = parse_info(line)
                        if p and p.get("nodes") is not None and p["nodes"] > budget:
                            over += 1
                            break
            row = {"threads": th, "budget": budget, "n": len(reported),
                   "reported_median": statistics.median(reported) if reported else None,
                   "reported_max": max(reported) if reported else None,
                   "ratio_median": round(statistics.median(ratios), 3) if ratios else None,
                   "ratio_max": round(max(ratios), 3) if ratios else None,
                   "searches_reporting_over_budget": over}
            rows.append(row)
            print(f"T{th:<2} N={budget:<8} n={row['n']:<3} median={row['reported_median']} "
                  f"max={row['reported_max']} ratio_median={row['ratio_median']} "
                  f"ratio_max={row['ratio_max']} over={over}", flush=True)
        e.close()
        print(flush=True)
    with open(out_path, "w") as fh:
        json.dump({"rows": rows, "exe": exe, "reps": reps,
                   "exe_sha256": os.popen(f"sha256sum {exe}").read().split()[0]}, fh, indent=2)
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
