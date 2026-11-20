#!/usr/bin/env python3
"""Count node-count differences between two depth_set row files."""
import sys
from pathlib import Path

def load(path):
    rows = {}
    for line in Path(path).read_text().splitlines():
        if not line.strip():
            continue
        parts = line.split()
        rows[int(parts[0])] = int(parts[1])
    return rows

a = load(sys.argv[1])
b = load(sys.argv[2])
keys = sorted(set(a) | set(b))
differ = [k for k in keys if a.get(k) != b.get(k)]
print(f"left={sys.argv[1]}")
print(f"right={sys.argv[2]}")
print(f"node_differ={len(differ)} of {len(keys)}")
