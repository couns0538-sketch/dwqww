#!/usr/bin/env python3
"""compare_o.py O1.rows O2.rows O3.rows — sums, first three, equality, differ count."""
import sys

def load(path):
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line:
                continue
            i, n = line.split("\t")
            rows.append((int(i), int(n)))
    return rows

def show(name, rows):
    nums = [n for _, n in rows]
    print(f"{name} positions {len(rows)} sum {sum(nums)} first {nums[0]} {nums[1]} {nums[2]}")

a, b, c = load(sys.argv[1]), load(sys.argv[2]), load(sys.argv[3])
show("O1", a)
show("O2", b)
show("O3", c)
same = sum(1 for (i, x), (j, y) in zip(a, b) if i == j and x == y)
print(f"O2 equal to O1 on {same} of {len(a)} positions")
differ = sum(1 for (i, x), (j, y) in zip(a, c) if x != y)
print(f"O3 differs from O1 on {differ} of {len(a)} positions")
