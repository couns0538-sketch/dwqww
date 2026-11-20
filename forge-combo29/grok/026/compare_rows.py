#!/usr/bin/env python3
"""Compare two .rows files position by position. Prints counts from the files."""

import sys
from pathlib import Path


def load(path: Path):
    rows = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        parts = line.split()
        rows[int(parts[0])] = (int(parts[1]), " ".join(parts[2:]), line)
    return rows


left = load(Path(sys.argv[1]))
right = load(Path(sys.argv[2]))
keys = sorted(set(left) | set(right))
differ = 0
missing = 0
for key in keys:
    if key not in left or key not in right:
        missing += 1
        print(f"missing {key}")
        continue
    if left[key][0] != right[key][0] or left[key][1] != right[key][1]:
        differ += 1
print(f"left {sys.argv[1]}")
print(f"right {sys.argv[2]}")
print(f"positions {len(keys)}")
print(f"differ {differ}")
print(f"missing {missing}")
print(f"equal {len(keys) - differ - missing}")
