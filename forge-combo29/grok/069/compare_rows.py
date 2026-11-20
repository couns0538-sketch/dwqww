#!/usr/bin/env python3
"""Compare two harness row files position by position.

Usage: compare_rows.py LEFT RIGHT
Prints how many positions differ in nodes, and the first differences.
"""
import sys
from pathlib import Path

def load(path: Path):
    rows = []
    for line in path.read_text().splitlines()[1:]:
        if not line.strip():
            continue
        idx, nodes, best, fen, info = line.split("\t", 4)
        rows.append((int(idx), int(nodes), best, fen))
    return rows

left = load(Path(sys.argv[1]))
right = load(Path(sys.argv[2]))
n = min(len(left), len(right))
differ = []
for i in range(n):
    if left[i][1] != right[i][1] or left[i][2] != right[i][2]:
        differ.append((left[i], right[i]))
print(f"left\t{sys.argv[1]}\tpositions\t{len(left)}\tnodes_sum\t{sum(r[1] for r in left)}")
print(f"right\t{sys.argv[2]}\tpositions\t{len(right)}\tnodes_sum\t{sum(r[1] for r in right)}")
print(f"compared\t{n}")
print(f"node_or_move_differ\t{len(differ)}")
print(f"identical\t{'yes' if len(left)==len(right) and len(differ)==0 else 'no'}")
for (li, ln, lb, lf), (ri, rn, rb, rf) in differ[:12]:
    print(f"diff\t{li}\tleft_nodes\t{ln}\tright_nodes\t{rn}\tleft_move\t{lb}\tright_move\t{rb}")
