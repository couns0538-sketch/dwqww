#!/usr/bin/env python3
"""Sum a .nodes file (index nodes) and print the first three rows plus the total."""
import sys

path = sys.argv[1]
rows = []
with open(path, encoding="utf-8") as handle:
    for line in handle:
        line = line.strip()
        if not line:
            continue
        index, nodes = line.split()
        rows.append((int(index), int(nodes)))
rows.sort()
total = sum(nodes for _, nodes in rows)
first = " ".join(str(nodes) for _, nodes in rows[:3])
print(f"positions {len(rows)}")
print(f"first3 {first}")
print(f"sum {total}")
