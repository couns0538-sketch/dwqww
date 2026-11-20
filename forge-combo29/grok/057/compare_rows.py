#!/usr/bin/env python3
"""Compare two suite row files. Prints equal count, differ count, both sums."""
import sys

def load(path):
    rows = []
    for line in open(path):
        line = line.strip()
        if not line:
            continue
        parts = line.split()
        rows.append((int(parts[0]), int(parts[1]), parts[2]))
    return rows

a = load(sys.argv[1])
b = load(sys.argv[2])
if len(a) != len(b):
    raise SystemExit(f"length {len(a)} vs {len(b)}")
differ = 0
for (i, na, da), (j, nb, db) in zip(a, b):
    if i != j:
        raise SystemExit(f"index {i} vs {j}")
    if na != nb or da != db:
        differ += 1
print(f"n {len(a)}")
print(f"sum_a {sum(n for _, n, _ in a)}")
print(f"sum_b {sum(n for _, n, _ in b)}")
print(f"differ {differ}")
print(f"equal {len(a) - differ}")
