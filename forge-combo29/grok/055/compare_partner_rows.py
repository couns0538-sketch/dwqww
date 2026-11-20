#!/usr/bin/env python3
"""Compare my measure.py table with seat 105's space-separated O rows."""
import sys
from pathlib import Path


def my_nodes(path: Path) -> list[int]:
    nodes = []
    for raw in path.read_text().splitlines():
        parts = raw.split("\t")
        if parts[0] in {"sum", "count"}:
            continue
        nodes.append(int(parts[1]))
    return nodes


def their_nodes(path: Path) -> list[int]:
    nodes = []
    for raw in path.read_text().splitlines():
        if not raw.strip():
            continue
        nodes.append(int(raw.split()[1]))
    return nodes


def main() -> int:
    left = my_nodes(Path(sys.argv[1]))
    right = their_nodes(Path(sys.argv[2]))
    n = max(len(left), len(right))
    differ = 0
    missing = abs(len(left) - len(right))
    for a, b in zip(left, right):
        if a != b:
            differ += 1
    print(f"mine {len(left)} theirs {len(right)} node_diff {differ} length_gap {missing}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
