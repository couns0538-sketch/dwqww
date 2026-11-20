#!/usr/bin/env python3
"""Compare my .nodes rows to the partner's space-separated node file, or to exe B."""
import sys
from pathlib import Path

def load(path: Path):
    rows = []
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        if "\t" in line:
            index, nodes, fen = line.split("\t", 2)
        else:
            index, nodes, fen = line.split(" ", 2)
        rows.append((int(index), int(nodes), fen))
    return rows

left = load(Path(sys.argv[1]))
right = load(Path(sys.argv[2]))
if len(left) != len(right):
    raise SystemExit(f"length {len(left)} vs {len(right)}")
differ = 0
for (i, a, fa), (j, b, fb) in zip(left, right):
    if i != j or fa != fb:
        raise SystemExit(f"fen mismatch at {i}")
    if a != b:
        differ += 1
print(f"left_sum {sum(n for _, n, _ in left)}")
print(f"right_sum {sum(n for _, n, _ in right)}")
print(f"positions {len(left)}")
print(f"differ {differ}")
print(f"same {len(left) - differ}")
