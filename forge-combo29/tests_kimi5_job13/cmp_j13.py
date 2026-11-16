#!/usr/bin/env python3
"""kimi5 job 13: compare each run's per-position nodes and best moves against the
S14 base run (i2). Prints 'N of 200 equal' for nodes and for best moves, per run.
Pure stdlib. Usage: cmp_j13.py rows"""
import json
import os
import sys

rows = sys.argv[1]
with open(os.path.join(rows, "i2.json")) as f:
    base = json.load(f)
bn, bb = base["per_position"], base["bestmove"]
n = len(bn)
print(f"base i2: n={n} nodes_sum={base['nodes_sum']} first3={bn[:3]}")
for tag in ["see0", "see99", "see100", "cfm0", "cfm1000", "cfd0", "cfd15"]:
    with open(os.path.join(rows, f"{tag}.json")) as f:
        r = json.load(f)
    rn, rb = r["per_position"], r["bestmove"]
    assert len(rn) == n, f"{tag}: length {len(rn)} != {n}"
    eq_nodes = sum(1 for a, b in zip(rn, bn) if a == b)
    eq_bm = sum(1 for a, b in zip(rb, bb) if a == b)
    diff_at = [i for i, (a, b) in enumerate(zip(rn, bn)) if a != b][:5]
    print(f"{tag}: nodes_sum={r['nodes_sum']} nodes {eq_nodes} of {n} equal, "
          f"best moves {eq_bm} of {n} equal" +
          (f" (first differing positions {diff_at})" if diff_at else ""))
