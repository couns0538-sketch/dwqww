#!/usr/bin/env python3
"""Print node and move differences between two depth_sum tsv files."""
import sys
from pathlib import Path


def load(path: Path):
    rows = []
    for line in path.read_text().splitlines():
        index, nodes, move = line.split("\t")
        rows.append((int(index), int(nodes), move))
    return rows


def main() -> int:
    left = load(Path(sys.argv[1]))
    right = load(Path(sys.argv[2]))
    n = min(len(left), len(right))
    node_diff = 0
    move_diff = 0
    for i in range(n):
        if left[i][1] != right[i][1]:
            node_diff += 1
        if left[i][2] != right[i][2]:
            move_diff += 1
    print(f"rows {len(left)} {len(right)}")
    print(f"node_diff {node_diff} of {n}")
    print(f"move_diff {move_diff} of {n}")
    print(f"sum {sum(row[1] for row in left)} {sum(row[1] for row in right)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
