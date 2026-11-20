#!/usr/bin/env python3
"""Print the node sum and the first three rows of a measure.py rows file."""
import sys

rows = []
for line in open(sys.argv[1]):
    parts = line.split()
    if not parts:
        continue
    rows.append(int(parts[1]))
print("n", len(rows))
print("sum", sum(rows))
print("first3", rows[0] if rows else None, rows[1] if len(rows) > 1 else None, rows[2] if len(rows) > 2 else None)
