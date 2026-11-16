#!/usr/bin/env python3
"""kimi5 job12 Step 3: T1/T2/T4/T7 against I2, per set.
Node sums, ratio, bootstrap 95% interval over POSITIONS (2,000 resamples,
seed 12, ratio of resampled sums, percentile 2.5/97.5 = indices 50/1950 of the
sorted 2,000), changed best moves vs I2. Prints how many files it read.
Usage: boot_j12.py <i2.json> <t1.json> <t2.json> <t4.json> <t7.json> <setname>
"""
import json
import random
import sys

i2 = json.load(open(sys.argv[1]))
ts = [json.load(open(f)) for f in sys.argv[2:6]]
name = sys.argv[6]

def boot(base, over, resamples=2000, seed=12):
    rng = random.Random(seed)
    n = len(base)
    ratios = []
    for _ in range(resamples):
        idx = [rng.randrange(n) for _ in range(n)]
        sb = sum(base[i] for i in idx)
        so = sum(over[i] for i in idx)
        ratios.append(so / sb)
    ratios.sort()
    return ratios[50], ratios[1950]

print(f"set {name}: read 5 files, {len(i2['per_position'])} positions")
print(f"I2 {i2['tag']} nodes_sum {i2['nodes_sum']}")
for t in ts:
    s = t["nodes_sum"]
    lo, hi = boot(i2["per_position"], t["per_position"])
    changed = sum(1 for x, y in zip(i2["bestmove"], t["bestmove"]) if x != y)
    print(f"{t['tag']}: nodes_sum {s} ratio {s / i2['nodes_sum']:.4f} "
          f"bootstrap95 [{lo:.4f}, {hi:.4f}] (2000 resamples, seed 12) "
          f"bestmoves changed {changed} of {len(t['bestmove'])}")
