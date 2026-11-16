#!/usr/bin/env python3
"""kimi5 job14 Step 3: tree ratios against a base rows file, per set.
Bootstrap 95% interval over POSITIONS (2,000 resamples, seed 12, ratio of
resampled sums, percentile 2.5/97.5 = indices 50/1950 of the sorted 2,000),
changed best moves vs base. Same method as boot_j12.py, any number of Ts.
Usage: boot_j14.py <base.json> <setname> <t1.json> [t2.json ...]
"""
import json
import random
import sys

base = json.load(open(sys.argv[1]))
name = sys.argv[2]
ts = [json.load(open(f)) for f in sys.argv[3:]]

def boot(b, over, resamples=2000, seed=12):
    rng = random.Random(seed)
    n = len(b)
    ratios = []
    for _ in range(resamples):
        idx = [rng.randrange(n) for _ in range(n)]
        sb = sum(b[i] for i in idx)
        so = sum(over[i] for i in idx)
        ratios.append(so / sb)
    ratios.sort()
    return ratios[50], ratios[1950]

print(f"set {name}: base {base['tag']} nodes_sum {base['nodes_sum']}, read {len(ts)} T files, "
      f"{len(base['per_position'])} positions")
for t in ts:
    s = t["nodes_sum"]
    lo, hi = boot(base["per_position"], t["per_position"])
    changed = sum(1 for x, y in zip(base["bestmove"], t["bestmove"]) if x != y)
    print(f"{t['tag']}: nodes_sum {s} ratio {s / base['nodes_sum']:.4f} "
          f"bootstrap95 [{lo:.4f}, {hi:.4f}] (2000 resamples, seed 12) "
          f"bestmoves changed {changed} of {len(t['bestmove'])}")
