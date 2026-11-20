#!/usr/bin/env python3
"""Compare my rows file to the partner's space-separated 'index nodes best' rows."""
import sys
from pathlib import Path


def mine(path: Path):
    rows = []
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        index, nodes, score, best, fen = line.split("\t", 4)
        rows.append((int(index), int(nodes), best))
    return rows


def theirs(path: Path):
    rows = []
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        index, nodes, best = line.split()
        rows.append((int(index), int(nodes), best))
    return rows


left = mine(Path(sys.argv[1]))
right = theirs(Path(sys.argv[2]))
if len(left) != len(right):
    raise SystemExit(f"length {len(left)} != {len(right)}")
differ = 0
for a, b in zip(left, right):
    if a != b:
        differ += 1
        if differ <= 8:
            print(f"differ index {a[0]} nodes {a[1]} vs {b[1]} best {a[2]} vs {b[2]}")
print(f"positions {len(left)}")
print(f"differ {differ}")
print(f"equal {len(left) - differ}")
