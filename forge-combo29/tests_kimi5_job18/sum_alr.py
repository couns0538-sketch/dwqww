#!/usr/bin/env python3
"""kimi5 job 18 step 3: sum the ALR v1 counter lines of the counting build over
ALL searches of a rows file; prints how many it summed. Known answers checked:
(1) the counting build's node sums equal Step 1's; (2) the sum over the classes
is at most the search's node count (per search and in total); (3) the planted
class d2 stays 0 under ARR 1. Run from tests_kimi5_job18/.
Usage: sum_alr.py rows/c_O_arr1_d12
"""
import json, re, sys

tag = sys.argv[1]
pat = re.compile(r"info string ALR v1 armed (\d+) d2 (\d+) d3_4 (\d+) d5_6 (\d+) d7_8 (\d+) d9_11 (\d+) "
                 r"d12plus (\d+) other (\d+)")
n = 0
tot = [0] * 8  # armed, d2, d3_4, d5_6, d7_8, d9_11, d12plus, other
worst = 0.0
worst_i = -1
with open(f"{tag}_full.txt") as f:
    lines = [pat.search(l) for l in f if "ALR v1" in l]
matches = [m for m in lines if m]
rows = json.load(open(f"{tag}.json"))
per = rows["per_position"]
assert len(matches) == len(per), f"{len(matches)} ALR lines vs {len(per)} positions"
for i, m in enumerate(matches):
    v = [int(g) for g in m.groups()]
    n += 1
    for j in range(8):
        tot[j] += v[j]
    cls_sum = sum(v[1:])
    if per[i] > 0:
        r = cls_sum / per[i]
        if r > worst:
            worst, worst_i = r, i
print(f"{tag}: summed {n} searches")
print(f"  armed {tot[0]}  d2 {tot[1]}  d3_4 {tot[2]}  d5_6 {tot[3]}  d7_8 {tot[4]}  d9_11 {tot[5]}  "
      f"d12plus {tot[6]}  other {tot[7]}")
print(f"  classes total {sum(tot[1:])}  nodes_sum {rows['nodes_sum']}  ratio {sum(tot[1:])/rows['nodes_sum']:.4f}")
print(f"  per-search max (classes/nodes) {worst:.4f} at position {worst_i}")
print(f"  d2 == 0: {'OK' if tot[1] == 0 else 'VIOLATED'};  d12plus: {tot[6]};  other: {tot[7]}")
