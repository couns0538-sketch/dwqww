#!/usr/bin/env python3
"""kimi5 job 32: aggregate a runner_j32 JSON: RANC class sums, HPMOVMAX maxima, DMAX and
last-iteration stats, equal-row count against a base JSON.
usage: agg_ranc.py <run.json> [base.json]"""
import json
import sys

j = json.load(open(sys.argv[1]))
ranc = {}
mm = [0, 0, 0]
dmax = []
for search in j.get('ranc', []):
    for cls, r, f in search:
        a = ranc.setdefault(cls, [0, 0])
        a[0] += r
        a[1] += f
for search in j.get('hpmovmax', []):
    if search:
        for d in range(3):
            mm[d] = max(mm[d], search[d])
for search in j.get('ran', []):
    if 'DMAX' in search:
        dmax.append(search['DMAX'][0])
it = j.get('last_iter', [])

def med(v):
    v = sorted(v)
    n = len(v)
    return (v[n // 2] if n % 2 else (v[n // 2 - 1] + v[n // 2]) / 2) if n else 0

print(f"# {j['tag']} go={j['go']} n={j['n_positions']} nodes_sum={j['nodes_sum']}")
print("class (0-3 out ld0/1/2/3+, 4-7 in) reached fired")
tot = [0, 0]
for c in range(8):
    r, f = ranc.get(c, [0, 0])
    tot[0] += r
    tot[1] += f
    print(f"  cls{c} {r} {f}")
print(f"  TOTAL {tot[0]} {tot[1]}")
print(f"movmax d1 {mm[0]} d2 {mm[1]} d3 {mm[2]}")
if dmax:
    print(f"DMAX min {min(dmax)} median {med(dmax)} max {max(dmax)}")
if it:
    print(f"last_iter min {min(it)} median {med(it)} max {max(it)}")
if len(sys.argv) > 2:
    b = json.load(open(sys.argv[2]))
    eq = sum(1 for i in range(j['n_positions'])
             if j['per_position'][i] == b['per_position'][i] and j['bestmove'][i] == b['bestmove'][i])
    print(f"equal rows vs {b['tag']}: {eq}/{j['n_positions']}")
