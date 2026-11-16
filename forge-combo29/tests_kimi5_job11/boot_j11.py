#!/usr/bin/env python3
"""kimi5 job11: T1 and T2 against I2, per set.
Node sums, ratio, bootstrap 95% interval over POSITIONS (2,000 resamples,
seed 11, ratio of resampled sums, percentile 2.5/97.5 = indices 50/1950 of the
sorted 2,000), changed best moves vs I2. Prints how many files it read.
Usage: boot_j11.py <i2.json> <t1.json> <t2.json> <setname>
"""
import json
import random
import sys

i2 = json.load(open(sys.argv[1]))
t1 = json.load(open(sys.argv[2]))
t2 = json.load(open(sys.argv[3]))
name = sys.argv[4]

def boot(base, over, resamples=2000, seed=11):
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

print(f"set {name}: read 3 files, {len(i2['per_position'])} positions")
base_sum = i2["nodes_sum"]
print(f"I2 {i2['tag']} nodes_sum {base_sum}")
for t in (t1, t2):
    s = t["nodes_sum"]
    lo, hi = boot(i2["per_position"], t["per_position"])
    changed = sum(1 for x, y in zip(i2["bestmove"], t["bestmove"]) if x != y)
    print(f"{t['tag']}: nodes_sum {s} ratio {s / base_sum:.4f} "
          f"bootstrap95 [{lo:.4f}, {hi:.4f}] (2000 resamples, seed 11) "
          f"bestmoves changed {changed} of {len(t['bestmove'])}")
