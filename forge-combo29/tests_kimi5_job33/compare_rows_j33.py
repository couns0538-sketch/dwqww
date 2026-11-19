#!/usr/bin/env python3
"""kimi5 job 33: compare two replay jsonl files row by row on the semantic fields
(depth, nodes, bestmove, hp27, hp27_nodes); print how many rows differ and the field sums.
Usage: compare_rows_j33.py <a.jsonl> <b.jsonl>
"""
import json
import sys

FIELDS = ["depth", "nodes", "bestmove", "hp27", "hp27_nodes"]

def load(path):
    rows = []
    with open(path) as f:
        for line in f:
            rows.append(json.loads(line))
    return rows

a = load(sys.argv[1])
b = load(sys.argv[2])
if len(a) != len(b):
    print(f"ROW COUNT DIFFERS: {len(a)} vs {len(b)}")
diff = 0
for i, (ra, rb) in enumerate(zip(a, b), start=1):
    if any(ra[k] != rb[k] for k in FIELDS):
        diff += 1
        if diff <= 3:
            print(f"row {i}: " + " ".join(f"{k} {ra[k]}!={rb[k]}" for k in FIELDS if ra[k] != rb[k]))
print(f"{diff} differing rows of {len(a)}  ({sys.argv[1]} vs {sys.argv[2]})")
for k in ["nodes", "hp27"]:
    print(f"sum {k}: {sum(r[k] for r in a)} vs {sum(r[k] for r in b)}")
