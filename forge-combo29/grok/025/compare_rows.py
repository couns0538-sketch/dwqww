#!/usr/bin/env python3
"""Compare two .rows files written by measure_depth.py. Prints counts only."""
import sys
from pathlib import Path


def load(path: Path) -> list[tuple[str, str, str]]:
    rows = []
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        index, nodes, move, fen = line.split("\t", 3)
        rows.append((index, nodes, move))
    return rows


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: compare_rows.py LEFT.rows RIGHT.rows", file=sys.stderr)
        return 2
    left = load(Path(sys.argv[1]))
    right = load(Path(sys.argv[2]))
    n = min(len(left), len(right))
    node_diff = 0
    move_diff = 0
    both = 0
    for i in range(n):
        ln, lm = left[i][1], left[i][2]
        rn, rm = right[i][1], right[i][2]
        nodes_differ = ln != rn
        moves_differ = lm != rm
        if nodes_differ:
            node_diff += 1
        if moves_differ:
            move_diff += 1
        if nodes_differ or moves_differ:
            both += 1
    left_sum = sum(int(row[1]) for row in left)
    right_sum = sum(int(row[1]) for row in right)
    print(f"left_n {len(left)} right_n {len(right)} compared {n}")
    print(f"left_sum {left_sum}")
    print(f"right_sum {right_sum}")
    print(f"node_differ {node_diff}")
    print(f"move_differ {move_diff}")
    print(f"either_differ {both}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
