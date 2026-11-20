#!/usr/bin/env python3
"""Compare two harness tsv files position by position. Prints the script's own counts."""
import sys

def load(path):
    rows = {}
    for line in open(path, encoding="utf-8"):
        parts = line.rstrip("\n").split("\t")
        if not parts or parts[0] in ("index", "SUM") or not parts[0].isdigit():
            continue
        rows[int(parts[0])] = (int(parts[1]), parts[2], parts[3] if len(parts) > 3 else "")
    return rows

left = load(sys.argv[1])
right = load(sys.argv[2])
keys = sorted(set(left) | set(right))
differ = 0
missing = 0
for key in keys:
    if key not in left or key not in right:
        missing += 1
        continue
    if left[key][0] != right[key][0] or left[key][1] != right[key][1]:
        differ += 1
print(f"left {len(left)} right {len(right)} missing {missing} differ {differ}")
