#!/usr/bin/env python3
"""Print a comparison table from measure_depth .rows files."""
import sys
from pathlib import Path


def load(path: Path):
    rows = []
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        index, nodes, move, _fen = line.split("\t", 3)
        rows.append((int(index), int(nodes), move))
    return rows


def main() -> int:
    if len(sys.argv) < 3:
        print("usage: summarize_rows.py LEFT.rows RIGHT.rows [label]", file=sys.stderr)
        return 2
    left = load(Path(sys.argv[1]))
    right = load(Path(sys.argv[2]))
    label = sys.argv[3] if len(sys.argv) > 3 else "compare"
    n = min(len(left), len(right))
    node_diff = sum(1 for i in range(n) if left[i][1] != right[i][1])
    move_diff = sum(1 for i in range(n) if left[i][2] != right[i][2])
    print(f"label {label}")
    print(f"left_file {sys.argv[1]}")
    print(f"right_file {sys.argv[2]}")
    print(f"n {n}")
    print(f"left_sum {sum(r[1] for r in left)}")
    print(f"right_sum {sum(r[1] for r in right)}")
    print(f"node_differ {node_diff} of {n}")
    print(f"move_differ {move_diff} of {n}")
    if n >= 3:
        print("left_first3 " + " ".join(str(left[i][1]) for i in range(3)))
        print("right_first3 " + " ".join(str(right[i][1]) for i in range(3)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
