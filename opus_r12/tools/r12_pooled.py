#!/usr/bin/env python3
"""r12_pooled.py - group vs group gain from an r12_speed.py runs.csv where each variant ran as several byte copies.

  r12_pooled.py RUNS.csv --x B1,B2,B3,B4 --y A1,A2,A3,A4 [--seed 20261030]

Per ABBA block: (sum nps of all X copies) / (sum nps of all Y copies) - 1; median over blocks and the bootstrap
(10000, seeded) one-sided 95% lower bound / 2-sided 95% CI, engine and CPU nps. Also prints each copy's mean nps
relative to its group mean (the per-file offsets the copies are there to average out).
"""
import argparse
import csv
import random
import statistics
from collections import defaultdict


def boot(g, seed, n=10000):
    rng = random.Random(seed)
    meds = sorted(statistics.median([rng.choice(g) for _ in g]) for _ in range(n))
    return meds[int(0.05 * n)], meds[int(0.025 * n)], meds[int(0.975 * n) - 1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("runs")
    ap.add_argument("--x", required=True)
    ap.add_argument("--y", required=True)
    ap.add_argument("--seed", type=int, default=20261030)
    a = ap.parse_args()
    xs, ys = a.x.split(","), a.y.split(",")
    blocks = defaultdict(lambda: defaultdict(list))
    for r in csv.DictReader(open(a.runs, encoding="utf-8")):
        if r["phase"] == "ABBA":
            blocks[(int(r["depth"]), int(r["block"]))][r["tag"]].append((float(r["nps"]), float(r["cpu_nps"])))
    for depth in sorted({d for d, _ in blocks}):
        for idx, metric in ((0, "engine_nps"), (1, "cpu_nps")):
            gains = []
            per_copy = defaultdict(list)
            for (d, b), runs in sorted(blocks.items()):
                if d != depth or not all(len(runs.get(t, [])) == 2 for t in xs + ys):
                    continue
                gains.append(sum(v[idx] for t in xs for v in runs[t]) / sum(v[idx] for t in ys for v in runs[t]) - 1)
                for t in xs + ys:
                    per_copy[t] += [v[idx] for v in runs[t]]
            if not gains:
                continue
            lb, lo, hi = boot(gains, a.seed)
            print("d%d %s vs %s %-10s n=%d median %+.2f%%  boot 1-sided 95%% LB %+.2f%%  2-sided [%+.2f%%, %+.2f%%]  blocks %s" % (
                depth, "+".join(xs), "+".join(ys), metric, len(gains), 100 * statistics.median(gains), 100 * lb,
                100 * lo, 100 * hi, " ".join("%+.2f" % (100 * g) for g in gains)))
            for grp in (xs, ys):
                mean = statistics.mean(v for t in grp for v in per_copy[t])
                print("    per-copy offset vs group mean: " + "  ".join(
                    "%s %+.2f%%" % (t, 100 * (statistics.mean(per_copy[t]) / mean - 1)) for t in grp))


if __name__ == "__main__":
    main()
