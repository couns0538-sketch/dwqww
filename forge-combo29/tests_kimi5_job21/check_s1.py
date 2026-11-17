#!/usr/bin/env python3
"""kimi5 job 21 Step 1 checker: per-position identities and changed-counts.
Reads rows/<setting>_<set>_d12.json written by runner_j20.py.
Prints, for O and G: identity lmr0 vs base (nodes AND bestmove per position),
all3 vs job20's all3 rows, and per ON setting the count of positions whose node
count changes vs base."""
import json
import os

JOB = os.path.dirname(os.path.abspath(__file__))
R = os.path.join(JOB, "rows")
J20 = os.path.join(JOB, "..", "tests_kimi5_job20", "rows")

def load(path):
    with open(path) as f:
        return json.load(f)

def cmp_rows(a, b):
    n_eq = sum(1 for x, y in zip(a["per_position"], b["per_position"]) if x == y)
    bm_eq = sum(1 for x, y in zip(a["bestmove"], b["bestmove"]) if x == y)
    both = sum(1 for x, y, u, v in zip(a["per_position"], b["per_position"],
                                       a["bestmove"], b["bestmove"]) if x == y and u == v)
    return n_eq, bm_eq, both, len(a["per_position"])

for s in ("O", "G"):
    base = load(f"{R}/base_{s}_d12.json")
    lmr0 = load(f"{R}/lmr0_{s}_d12.json")
    n, b, both, tot = cmp_rows(lmr0, base)
    print(f"identity lmr0==base {s}: nodes {n}/{tot} bestmove {b}/{tot} both {both}/{tot}")
    a3 = load(f"{R}/all3_{s}_d12.json")
    a3j = load(f"{J20}/all3_{s}_d12.json")
    n, b, both, tot = cmp_rows(a3, a3j)
    print(f"identity all3==job20 all3 {s}: nodes {n}/{tot} bestmove {b}/{tot} both {both}/{tot}")
    for st in ("lmr2048", "lmr8192", "cap4"):
        r = load(f"{R}/{st}_{s}_d12.json")
        ch = sum(1 for x, y in zip(r["per_position"], base["per_position"]) if x != y)
        bmch = sum(1 for x, y in zip(r["bestmove"], base["bestmove"]) if x != y)
        print(f"{st} vs base {s}: node-changed {ch}/{tot} bestmove-changed {bmch}/{tot} sum {r['nodes_sum']}")
