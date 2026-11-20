#!/usr/bin/env python3
"""Compare two .nodes files position by position. Prints the pasted table."""
import sys

def load(path):
    rows = {}
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            index, nodes = line.split()
            rows[int(index)] = int(nodes)
    return rows

left = load(sys.argv[1])
right = load(sys.argv[2])
keys = sorted(set(left) | set(right))
differ = []
missing = []
for key in keys:
    if key not in left or key not in right:
        missing.append(key)
        continue
    if left[key] != right[key]:
        differ.append((key, left[key], right[key]))
print(f"left {sys.argv[1]}")
print(f"right {sys.argv[2]}")
print(f"positions {len(keys)}")
print(f"missing {len(missing)}")
print(f"differ {len(differ)} of {len(keys)}")
for key, a, b in differ[:20]:
    print(f"pos {key} left {a} right {b}")
if len(differ) > 20:
    print(f"... {len(differ) - 20} more")
