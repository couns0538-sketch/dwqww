#!/usr/bin/env python3
"""Compare two node tsv files written by search_set.py. Prints differ count and sums."""
import sys

def load(path):
    rows = {}
    for line in open(path):
        line = line.strip()
        if not line or line.startswith("index"):
            continue
        index, nodes = line.split("\t")
        rows[int(index)] = int(nodes)
    return rows

base, other, label = sys.argv[1], sys.argv[2], sys.argv[3]
a, b = load(base), load(other)
keys = sorted(set(a) | set(b))
differ = [k for k in keys if a.get(k) != b.get(k)]
print(f"{label} positions {len(keys)} differ {len(differ)} sum_base {sum(a.values())} sum_other {sum(b.values())}")
