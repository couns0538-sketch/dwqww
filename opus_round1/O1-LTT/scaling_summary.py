#!/usr/bin/env python3
"""Combine the scaling.py TSVs of .github/workflows/opus-o1-ltt.yml into one table: for every thread count,
LocklessTT off vs on, the mean time-to-depth over the runs (all positions), mean nodes, NPS and the on/off
ratios. Input files: <dir>/scaling_t<threads>_<off|on>.tsv with columns threads, run, position, seconds, nodes.
usage: scaling_summary.py <dir>"""
import collections
import pathlib
import statistics
import sys

root = pathlib.Path(sys.argv[1])
rows = {}
for path in sorted(root.glob("scaling_t*_*.tsv")):
    threads, mode = path.stem.split("_")[1][1:], path.stem.split("_")[2]
    per_run = collections.defaultdict(lambda: [0.0, 0])
    with path.open(encoding="utf-8") as f:
        next(f)
        for line in f:
            t, run, _pos, seconds, nodes = line.rstrip("\n").split("\t")
            per_run[run][0] += float(seconds)
            per_run[run][1] += int(nodes)
    times = [v[0] for v in per_run.values()]
    nodes = [v[1] for v in per_run.values()]
    rows[(int(threads), mode)] = (statistics.mean(times), statistics.stdev(times) if len(times) > 1 else 0.0,
                                  statistics.mean(nodes), sum(nodes) / sum(times), len(times))
print("threads | mode | runs | time-to-depth mean (sd) | nodes mean | NPS | on/off time | on/off NPS")
for threads in sorted({k[0] for k in rows}):
    off = rows.get((threads, "off"))
    for mode in ("off", "on"):
        r = rows.get((threads, mode))
        if r is None:
            continue
        ratio = ""
        if mode == "on" and off is not None:
            ratio = f"{r[0] / off[0]:.3f} | {r[3] / off[3]:.3f}"
        print(f"{threads:7d} | {mode:4} | {r[4]:4d} | {r[0]:8.2f}s ({r[1]:5.2f}) | {r[2]:12.0f} | {r[3]:10.0f} | {ratio}")
