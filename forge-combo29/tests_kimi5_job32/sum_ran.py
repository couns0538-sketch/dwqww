#!/usr/bin/env python3
"""kimi5 job 29: sum the RAN counters of one _full.txt over its searches.
usage: sum_ran.py <full.txt> -> one line per id: ID reached fired (sums)."""
import sys
from collections import defaultdict

sums = defaultdict(lambda: [0, 0])
n_searches = 0
with open(sys.argv[1]) as f:
    for line in f:
        if line.startswith("info string RAN "):
            _, _, _, cid, reached, fired = line.split()
            sums[cid][0] += int(reached)
            sums[cid][1] += int(fired)
        elif line.startswith("bestmove"):
            n_searches += 1
print(f"# {sys.argv[1]} searches={n_searches}")
for cid in ("HP", "NULL", "NULLQ", "DRAW", "CAPFUT", "DMAX"):
    r, f_ = sums.get(cid, [0, 0])
    print(f"{cid} {r} {f_}")
