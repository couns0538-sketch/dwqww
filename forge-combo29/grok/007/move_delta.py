#!/usr/bin/env python3
"""Compare node counts and best moves in two rows files."""
import sys
from pathlib import Path


def load(path: Path) -> list[tuple[str, str]]:
    rows = []
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        _index, nodes, move = line.split("\t")
        rows.append((nodes, move))
    return rows


def main() -> int:
    left = load(Path(sys.argv[1]))
    right = load(Path(sys.argv[2]))
    if len(left) != len(right):
        print(f"length {len(left)} {len(right)}")
        return 1
    node_diff = 0
    move_diff = 0
    up = 0
    down = 0
    net = 0
    for a, b in zip(left, right):
        delta = int(b[0]) - int(a[0])
        net += delta
        if delta > 0:
            up += 1
        elif delta < 0:
            down += 1
        if a[0] != b[0]:
            node_diff += 1
        if a[1] != b[1]:
            move_diff += 1
    print(
        f"positions {len(left)} node_differ {node_diff} move_differ {move_diff} "
        f"nodes_up {up} nodes_down {down} net_nodes {net}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
