#!/usr/bin/env python3
"""Compare two harness TSVs by index. Columns after the header may be
index, nodes, bestmove, fen, and an optional info field.
"""
import sys
from pathlib import Path

def load(path: Path):
    rows = {}
    for line in path.read_text().splitlines()[1:]:
        if not line.strip():
            continue
        parts = line.split("\t")
        rows[int(parts[0])] = (int(parts[1]), parts[2], parts[3])
    return rows

left = load(Path(sys.argv[1]))
right = load(Path(sys.argv[2]))
keys = sorted(set(left) & set(right))
node_diff = move_diff = 0
shown = 0
for key in keys:
    ln, lb, lf = left[key]
    rn, rb, rf = right[key]
    if ln != rn:
        node_diff += 1
    if lb != rb:
        move_diff += 1
    if (ln != rn or lb != rb) and shown < 8:
        print(f"diff\t{key}\tleft\t{ln}\t{lb}\tright\t{rn}\t{rb}\tfen_same\t{lf == rf}")
        shown += 1
print(f"left_n\t{len(left)}\tright_n\t{len(right)}\tcompared\t{len(keys)}")
print(f"left_sum\t{sum(v[0] for v in left.values())}")
print(f"right_sum\t{sum(v[0] for v in right.values())}")
print(f"node_differ\t{node_diff}")
print(f"move_differ\t{move_diff}")
print(f"identical\t{'yes' if len(left)==len(right) and node_diff==0 and move_diff==0 else 'no'}")
first = [right[i][0] for i in (1, 2, 3) if i in right]
print("right_first3\t" + "\t".join(str(n) for n in first))
