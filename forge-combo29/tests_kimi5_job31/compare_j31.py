#!/usr/bin/env python3
"""kimi5 job 31: compare a run's per_position/bestmove lists against another json.
Usage: compare_j31.py <a.json> <b.json> <label>
Prints counts equal for nodes, bestmove, and both, plus the first difference if any.
"""
import json
import sys

a = json.load(open(sys.argv[1]))
b = json.load(open(sys.argv[2]))
label = sys.argv[3] if len(sys.argv) > 3 else ""
pa, pb = a["per_position"], b["per_position"]
ba, bb = a["bestmove"], b["bestmove"]
n = min(len(pa), len(pb))
eqn = sum(1 for i in range(n) if pa[i] == pb[i])
eqb = sum(1 for i in range(n) if ba[i] == bb[i])
both = sum(1 for i in range(n) if pa[i] == pb[i] and ba[i] == bb[i])
print(f"{label}: positions {len(pa)} vs {len(pb)}; nodes equal {eqn}/{n}; "
      f"bestmove equal {eqb}/{n}; both {both}/{n}; sums {sum(pa)} vs {sum(pb)}")
for i in range(n):
    if pa[i] != pb[i] or ba[i] != bb[i]:
        print(f"  first DIFF at {i}: nodes {pa[i]} vs {pb[i]}, bestmove {ba[i]} vs {bb[i]}")
        break
