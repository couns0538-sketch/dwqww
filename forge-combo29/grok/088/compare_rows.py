#!/usr/bin/env python3
"""Compare two .rows files position by position. Prints the count that differ."""
import sys

def load(path):
    rows = {}
    for line in open(path):
        index, nodes, fen = line.rstrip("\n").split("\t", 2)
        rows[int(index)] = (int(nodes), fen)
    return rows

left = load(sys.argv[1])
right = load(sys.argv[2])
keys = sorted(set(left) | set(right))
differ = 0
missing = 0
for key in keys:
    if key not in left or key not in right:
        missing += 1
        print(f"MISSING {key}")
        continue
    if left[key][1] != right[key][1]:
        print(f"FEN {key}")
        missing += 1
        continue
    if left[key][0] != right[key][0]:
        differ += 1
        if differ <= 8:
            print(f"DIFF {key} a={left[key][0]} b={right[key][0]}")
print(f"positions={len(keys)} differ={differ} missing={missing}")
