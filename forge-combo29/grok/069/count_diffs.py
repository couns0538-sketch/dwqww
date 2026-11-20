#!/usr/bin/env python3
"""Count node differences and best-move differences between two row files."""
import sys
from pathlib import Path

def load(path):
    rows = []
    for line in Path(path).read_text().splitlines()[1:]:
        if not line.strip():
            continue
        idx, nodes, best, fen, info = line.split("\t", 4)
        rows.append((int(nodes), best))
    return rows

left = load(sys.argv[1])
right = load(sys.argv[2])
node_diff = move_diff = 0
for (ln, lb), (rn, rb) in zip(left, right):
    if ln != rn:
        node_diff += 1
    if lb != rb:
        move_diff += 1
print(f"positions\t{len(left)}")
print(f"node_differ\t{node_diff}")
print(f"move_differ\t{move_diff}")
print(f"same_nodes\t{len(left) - node_diff}")
