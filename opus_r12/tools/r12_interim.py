#!/usr/bin/env python3
"""r12_interim.py - per-block gains from a running r12_speed.py runs.csv (finished blocks only), for the stop rule.

  r12_interim.py RUNS.csv --x A --ref L9 [--ref D8 ...]

Prints, per depth and reference, the gain of X (sum nps X / sum nps REF - 1) for every complete ABBA block and the
median so far (engine nps and CPU nps). Read-only.
"""
import argparse
import csv
import statistics
from collections import defaultdict


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("runs")
    ap.add_argument("--x", required=True)
    ap.add_argument("--ref", action="append", required=True)
    a = ap.parse_args()
    blocks = defaultdict(lambda: defaultdict(list))
    for r in csv.DictReader(open(a.runs, encoding="utf-8")):
        if r["phase"] == "ABBA":
            blocks[(int(r["depth"]), int(r["block"]))][r["tag"]].append((float(r["nps"]), float(r["cpu_nps"])))
    for ref in a.ref:
        for depth in sorted({d for d, _ in blocks}):
            for idx, metric in ((0, "engine_nps"), (1, "cpu_nps")):
                gains = []
                for (d, b), runs in sorted(blocks.items()):
                    if d != depth or len(runs.get(a.x, [])) != 2 or len(runs.get(ref, [])) != 2:
                        continue
                    den = sum(v[idx] for v in runs[ref])
                    if den > 0:
                        gains.append(sum(v[idx] for v in runs[a.x]) / den - 1.0)
                if gains:
                    print("d%d %s vs %s %-10s blocks %d median %+.2f%%  [%s]" % (
                        depth, a.x, ref, metric, len(gains), 100 * statistics.median(gains),
                        " ".join("%+.2f" % (100 * g) for g in gains)))


if __name__ == "__main__":
    main()
