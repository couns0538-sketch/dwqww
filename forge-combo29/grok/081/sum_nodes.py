#!/usr/bin/env python3
"""Print a node-sum table from a .nodes.txt file written by measure_set.py."""
import sys

path = sys.argv[1]
rows = []
with open(path, "r", encoding="utf-8") as handle:
    for line in handle:
        text = line.strip()
        if text:
            rows.append(int(text))
total = sum(rows)
print("file %s" % path)
print("positions %d" % len(rows))
print("sum %d" % total)
shown = " ".join(str(rows[i]) for i in range(min(3, len(rows))))
print("first3 %s" % shown)
