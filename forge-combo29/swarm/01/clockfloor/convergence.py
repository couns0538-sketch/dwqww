#!/usr/bin/env python3
"""swarm seat 01: does the node-ratio median CONVERGE, or drift with n? (S-C63)

The population run answers a question a single number cannot: **is the stride sample's median an estimate that happens to
be close, or is it biased?** Those look identical from one comparison and are different facts.

Method: the median of the first n pairs, for n on a doubling ladder, against the median of ALL pairs collected so far.
  * a biased sample shows a **monotone drift** in the running median as n grows, settling only when n is large;
  * an unbiased sample shows the running median **wandering inside a band** that narrows with sqrt(n) and does not trend.

The doubling ladder is the point: at n = 116 (the original stride sample) a bias is invisible, because 116 is one point.
At n = 512, 1024, 4096 the same median either holds or walks away, and the walk is the evidence.

Also reports, at each rung, the fraction above 2x and the mean — the sample's tail claims are about those.

Usage: convergence.py <pairs.jsonl> [--rungs 116,256,512,1024,2048,4096,8192]
"""
import json
import statistics
import sys
from pathlib import Path


def q(v, p):
    v = sorted(v)
    k = (len(v) - 1) * p
    f = int(k)
    c = min(f + 1, len(v) - 1)
    return v[f] + (v[c] - v[f]) * (k - f)


def main():
    src = sys.argv[1]
    rungs = [116, 256, 512, 1024, 2048, 4096, 8192]
    if "--rungs" in sys.argv:
        rungs = [int(x) for x in sys.argv[sys.argv.index("--rungs") + 1].split(",")]

    rows = []
    for line in Path(src).read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        if r.get("ratio") and r.get("node_ratio"):
            rows.append(r)

    n = len(rows)
    print("pairs available: %d" % n)
    if n < 50:
        print("too few to say anything about convergence.")
        return 1

    nr_all = [r["node_ratio"] for r in rows]
    wr_all = [r["ratio"] for r in rows]

    print()
    print("%-7s %-9s %-9s %-9s %-9s %-9s %s"
          % ("n", "node_med", "wall_med", "node_mean", "node_Q3", ">2x %", "note"))
    prev = None
    print_lines = []
    for rung in rungs:
        if rung > n:
            print_lines.append("%-7s (not reached yet)" % rung)
            continue
        # RANDOM subsample, not a prefix. My first version used rows[:rung], and these FENs are a GAME SEQUENCE -
        # each advances the previous, opening -> endgame - so a prefix is a different PHASE OF THE GAME at every rung,
        # not a smaller sample of the same population. The "monotone drift" it showed was game phase, not sampling
        # error. Seeded so the ladder is reproducible.
        import random as _r
        sub = _r.Random(1234).sample(rows, rung)
        nr = [r["node_ratio"] for r in sub]
        wr = [r["ratio"] for r in sub]
        med = statistics.median(nr)
        drift = "" if prev is None else "%+.4f" % (med - prev)
        print_lines.append("%-7d %-9.4f %-9.4f %-9.4f %-9.3f %-9.1f %s"
                           % (rung, med, statistics.median(wr), statistics.mean(nr),
                              q(nr, 0.75), 100.0 * sum(1 for x in nr if x > 2) / len(nr), drift))
        prev = med
    for l in print_lines:
        print(l)

    print()
    full_med = statistics.median(nr_all)
    print("median over ALL %d pairs: %.4f" % (n, full_med))
    print("NOTE: each rung is a SEEDED RANDOM subsample. These FENs are a game sequence (each advances the previous),")
    print("      so a prefix would be a different game PHASE at every rung - which is what my first version measured.")
    # the honest test: is the first-116 median within the spread the later rungs show?
    early = statistics.median([r["node_ratio"] for r in rows[:min(116, n)]])
    print("median over the first 116 : %.4f   (difference from full: %+.4f)" % (early, early - full_med))

    if n >= 1024:
        late = statistics.median([r["node_ratio"] for r in rows[:n // 2]])
        later = statistics.median([r["node_ratio"] for r in rows[n // 2:]])
        print("first half median         : %.4f" % late)
        print("second half median        : %.4f" % later)
        print()
        if abs(late - later) <= 0.02:
            print("VERDICT: the median is STABLE across halves of the population (difference %.4f). The stride"
                  % abs(late - later))
            print("  sample's estimate reproduces, and the tail claims rest on a property of the population.")
        else:
            print("VERDICT: the median MOVES between halves (%.4f vs %.4f) - the population is not homogeneous,"
                  % (late, later))
            print("  so which half a sample came from matters and the stride sample's figure is sample-dependent.")
    else:
        print("(need at least 1024 pairs for the half-split test; run longer)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
