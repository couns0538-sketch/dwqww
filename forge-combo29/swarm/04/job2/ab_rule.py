#!/usr/bin/env python3
"""ab_rule.py — turn the measured Threads-4 score deviations into a practical rule for threaded A/B tests.

The question a tuner asks: "I want to detect an effect of E centipawns at Threads 4 on this machine.
How many repetitions of each arm do I need before the thread noise stops drowning E?"

Method, all from measured data (no invented constants):
  * The per-run score at Threads 4 has a spread. I use the deviations of my 30 Threads-4 runs from the
    one-thread score at the same depth (job2/raw/pc20_ord.jsonl and pc20_hi.jsonl), pooled over depths
    12..16. That pooled set is the noise model.
  * sd of one run is computed from those deviations. Since the one-thread value is the reference (and is
    bit-reproducible here), |deviation| is the per-run error.
  * For an A/B of two arms each with n runs, the standard error of the difference of means is
    sd * sqrt(2/n). To detect E with ~80% power at alpha=0.05 two-sided, need
        E >= (1.96 + 0.84) * sd * sqrt(2/n)
    so  n >= 2 * (2.80 * sd / E)^2, rounded up.
  * I also report the WORST-CASE single-run deviation, because a tuner who runs one game per arm is
    exposed to that, not to the mean.

This is a planning calculation from a measured sd, not a measurement itself: it says how many runs the
noise REQUIRES, and it is only as good as the sd. The script prints the sd it used so the reader can
check the arithmetic.

Usage: ab_rule.py [--rawdir ...]
"""
import glob
import json
import math
import os
import statistics
import sys

RAW = "/agent/repos/dwqww/forge-combo29/swarm/04/job2/raw"


def load_devs(rawdir):
    ref = {}
    mt = {}
    for path in sorted(glob.glob(os.path.join(rawdir, "*.jsonl"))):
        for line in open(path):
            try:
                r = json.loads(line)
            except Exception:
                continue
            if "threads" not in r or "depth" not in r or "score" not in r:
                continue
            if not isinstance(r.get("score"), int):
                continue          # mate scores are excluded: this rule is for centipawn effects
            # The rule is for TUNING on ordinary game positions, so the tactically extreme hang FEN is
            # kept out of the noise model: mixing a position whose score crosses into mate with ordinary
            # middlegame positions would overstate the noise a tuner actually faces.
            if "5R2/1p5k" in r.get("fen", ""):
                continue
            key = (os.path.basename(path), r["depth"])
            if r["threads"] == 1:
                ref.setdefault(key, []).append(r["score"])
            elif r["threads"] >= 4:
                mt.setdefault(key, []).append(r["score"])
    devs = []
    rows = []
    for key, vals in sorted(mt.items()):
        rv = ref.get(key)
        if not rv:
            continue
        base = rv[0]
        for v in vals:
            devs.append(v - base)
        rows.append((key[0], key[1], base, min(vals), max(vals),
                     max(abs(v - base) for v in vals)))
    return devs, rows


def main():
    rawdir = sys.argv[1] if len(sys.argv) > 1 else RAW
    devs, rows = load_devs(rawdir)
    if not devs:
        print("no paired reference/multi-thread data found in %s" % rawdir)
        sys.exit(1)

    print("== per-depth Threads-4 scores against the one-thread reference ==")
    print("%-28s %5s %8s %8s %8s %8s" % ("file", "depth", "threads1", "mt_min", "mt_max", "maxdev"))
    for f, d, base, lo, hi, dev in rows:
        print("%-28s %5d %8d %8d %8d %8d" % (f, d, base, lo, hi, dev))

    sd = statistics.stdev(devs) if len(devs) > 1 else 0.0
    worst = max(abs(d) for d in devs)
    rng = max(devs) - min(devs)
    print()
    print("n runs=%d  mean deviation=%.1f cp  sd=%.1f cp  worst |deviation|=%d cp  range=%d cp"
          % (len(devs), statistics.mean(devs), sd, worst, rng))

    print()
    print("== runs per arm needed to detect an effect E (80%% power, alpha=0.05 two-sided) ==")
    print("   n = 2 * (2.80 * sd / E)^2, with sd = %.1f cp measured above" % sd)
    print("%10s %10s" % ("effect E", "n per arm"))
    for e in (10, 20, 25, 30, 50, 100):
        n = max(1, math.ceil(2 * (2.80 * sd / e) ** 2))
        print("%8d cp %10d" % (e, n))

    print()
    print("== what one run per arm can and cannot tell you ==")
    print("A single Threads-4 run can differ from the truth by up to %d cp (worst measured)." % worst)
    print("So an A/B of ONE run per arm cannot resolve an effect smaller than about %d cp," % worst)
    print("and even then only by luck. Effects below ~%d cp need the repetitions above." % worst)


if __name__ == "__main__":
    main()
