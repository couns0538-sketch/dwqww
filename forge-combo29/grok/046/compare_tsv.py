#!/usr/bin/env python3
"""Compare two measurement tsv files position by position."""
import sys
from pathlib import Path

def load(path: Path):
    rows = {}
    for line in path.read_text().splitlines()[1:]:
        if not line.strip():
            continue
        index, nodes, move, fen = line.split("\t", 3)
        rows[int(index)] = (int(nodes), move, fen)
    return rows

left = load(Path(sys.argv[1]))
right = load(Path(sys.argv[2]))
keys = sorted(set(left) | set(right))
node_diff = 0
move_diff = 0
fen_diff = 0
missing = 0
for key in keys:
    if key not in left or key not in right:
        missing += 1
        continue
    ln, lm, lf = left[key]
    rn, rm, rf = right[key]
    if ln != rn:
        node_diff += 1
    if lm != rm:
        move_diff += 1
    if lf != rf:
        fen_diff += 1
print(f"left {sys.argv[1]}")
print(f"right {sys.argv[2]}")
print(f"positions {len(keys)}")
print(f"missing {missing}")
print(f"node_diff {node_diff}")
print(f"move_diff {move_diff}")
print(f"fen_diff {fen_diff}")
