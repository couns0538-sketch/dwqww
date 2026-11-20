#!/usr/bin/env python3
"""Compare two depth_set row files. Prints how many positions differ and the first differences."""
import sys
from pathlib import Path

def load(path: Path):
    rows = {}
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        parts = line.split()
        rows[int(parts[0])] = line
    return rows

a = load(Path(sys.argv[1]))
b = load(Path(sys.argv[2]))
keys = sorted(set(a) | set(b))
differ = []
for k in keys:
    if a.get(k) != b.get(k):
        differ.append(k)
print(f"left={sys.argv[1]}")
print(f"right={sys.argv[2]}")
print(f"positions={len(keys)}")
print(f"differ={len(differ)} of {len(keys)}")
for k in differ[:8]:
    print(f"L {a.get(k)}")
    print(f"R {b.get(k)}")
