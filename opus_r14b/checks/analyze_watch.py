#!/usr/bin/env python3
"""analyze_watch.py WATCH.tsv - Opus R14-B: does the live npt trainer's GPU use follow the CPU share it gets?
Reads the read-only watcher log of trainer_watch.sh (time, trainer pid, mask, priority, trainer cores, cores of the
other processes allowed on its CPUs, busiest other, GPU util mean / p50 over the 5 minutes before the sample).
Prints, per regime (one trainer process on one CPU mask) and pooled: sample count, time span, mean trainer cores, mean
cores of the others on its mask, mean GPU util, Pearson r between trainer cores and GPU util (rough 95 % interval via
Fisher's z) and mean GPU util per trainer-cores band. Regimes differ in CPU arrangement (e.g. mask 0x3 vs 0xF), so a
pooled r mixes them: read the per-regime lines first.
Descriptive only: a correlation here is not proof that CPU limits the GPU (both can follow the trainer's phase).
"""
import math
import statistics
import sys


def pearson(xs, ys):
    if len(xs) < 3 or len(set(xs)) < 2 or len(set(ys)) < 2:
        return float("nan"), float("nan"), float("nan")
    r = statistics.correlation(xs, ys)
    lo = hi = float("nan")
    if len(xs) > 3 and abs(r) < 1:
        z, se = math.atanh(r), 1 / math.sqrt(len(xs) - 3)
        lo, hi = math.tanh(z - 1.96 * se), math.tanh(z + 1.96 * se)
    return r, lo, hi


def describe(name, rows):
    cores = [r["cores"] for r in rows]
    others = [r["others"] for r in rows]
    gpu = [r["gpu"] for r in rows]
    r, lo, hi = pearson(cores, gpu)
    print(f"{name}: {len(rows)} samples {rows[0]['time']} -> {rows[-1]['time']}")
    print(f"  trainer cores mean {statistics.fmean(cores):.2f} (min {min(cores):.2f}, max {max(cores):.2f}); others on "
          f"its mask {statistics.fmean(others):.2f} cores; GPU util mean {statistics.fmean(gpu):.1f} %")
    print(f"  Pearson r(trainer cores, GPU util) = {r:.2f} (95 % CI {lo:.2f} .. {hi:.2f}, Fisher z)")
    for band, a, b in (("< 0.5 cores", 0, 0.5), ("0.5-1.0", 0.5, 1.0), ("1.0-1.5", 1.0, 1.5), (">= 1.5", 1.5, 99)):
        g = [x["gpu"] for x in rows if a <= x["cores"] < b]
        if g:
            print(f"    trainer {band:11s}: {len(g):3d} samples, GPU util mean {statistics.fmean(g):.1f} %")


def main(path):
    rows = []
    for line in open(path, encoding="utf-8").read().splitlines()[1:]:
        f = line.split("\t")
        if len(f) < 9 or f[1] == "none" or f[7] in ("na", ""):
            continue
        try:
            rows.append({"time": f[0], "pid": f[1], "mask": f[2], "cores": float(f[4]), "others": float(f[5]),
                         "gpu": float(f[7])})
        except ValueError:
            continue
    if len(rows) < 3:
        print(f"{len(rows)} usable samples - too few")
        return 1
    regimes = {}
    for r in rows:
        regimes.setdefault((r["pid"], r["mask"]), []).append(r)
    for (pid, mask), g in regimes.items():
        describe(f"regime trainer pid {pid}, mask {mask}", g)
    describe("pooled (mixes the regimes above)", rows)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
