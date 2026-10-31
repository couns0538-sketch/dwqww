#!/usr/bin/env python3
"""r12_pair_from_aa.py - X vs Y from the A/A blocks of r12_speed.py (they hold X, X', Y, Y' in a palindrome).

  r12_pair_from_aa.py RUNS.csv --x B --y A

Prints per depth: X/Y (originals), X'/Y' (copies) and pooled (X+X')/(Y+Y') gains per A/A block, engine and CPU nps.
A second, file-independent look at X vs Y when byte copies show per-file timing offsets (R5B lesson).
"""
import argparse
import csv
import statistics
from collections import defaultdict


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("runs")
    ap.add_argument("--x", required=True)
    ap.add_argument("--y", required=True)
    a = ap.parse_args()
    blocks = defaultdict(lambda: defaultdict(list))
    for r in csv.DictReader(open(a.runs, encoding="utf-8")):
        if r["phase"] == "AA":
            blocks[(int(r["depth"]), int(r["block"]))][r["tag"]].append((float(r["nps"]), float(r["cpu_nps"])))
    for depth in sorted({d for d, _ in blocks}):
        for idx, metric in ((0, "engine_nps"), (1, "cpu_nps")):
            rows = {"orig": [], "copy": [], "pooled": []}
            for (d, b), runs in sorted(blocks.items()):
                if d != depth:
                    continue
                s = lambda t: sum(v[idx] for v in runs[t])
                rows["orig"].append(s(a.x) / s(a.y) - 1)
                rows["copy"].append(s(a.x + "'") / s(a.y + "'") - 1)
                rows["pooled"].append((s(a.x) + s(a.x + "'")) / (s(a.y) + s(a.y + "'")) - 1)
            for k, g in rows.items():
                print("d%d %s vs %s %-10s %-6s median %+.2f%% [%s]" % (
                    depth, a.x, a.y, metric, k, 100 * statistics.median(g), " ".join("%+.2f" % (100 * x) for x in g)))


if __name__ == "__main__":
    main()
