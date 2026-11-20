#!/usr/bin/env python3
"""Compare two node rows files. Prints equals, differs, and the first mismatches."""
import sys
from pathlib import Path

def load(path):
    rows = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        index, nodes, best = line.split("\t")
        rows.append((int(index), int(nodes), best))
    return rows

left = load(sys.argv[1])
right = load(sys.argv[2])
if len(left) != len(right):
    print(f"length {len(left)} {len(right)}")
    sys.exit(1)
differ = 0
shown = 0
for a, b in zip(left, right):
    if a != b:
        differ += 1
        if shown < 8:
            print(f"differ index {a[0]} left {a[1]} {a[2]} right {b[1]} {b[2]}")
            shown += 1
print(f"count {len(left)} differ {differ} equal {len(left) - differ}")
