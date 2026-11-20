#!/usr/bin/env python3
"""Compare per-position node files. Usage: compare_nodes.py LEFT RIGHT"""
import sys
from pathlib import Path


def load(path: Path) -> list[tuple[str, str, str]]:
    rows = []
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        index, nodes, move, *fen = line.split()
        rows.append((index, nodes, move))
    return rows


def main() -> None:
    left = load(Path(sys.argv[1]))
    right = load(Path(sys.argv[2]))
    if len(left) != len(right):
        raise SystemExit(f"length {len(left)} vs {len(right)}")
    differ = 0
    first = []
    for a, b in zip(left, right):
        if a[0] != b[0]:
            raise SystemExit(f"index mismatch {a[0]} {b[0]}")
        if a[1] != b[1] or a[2] != b[2]:
            differ += 1
            if len(first) < 8:
                first.append(f"{a[0]} left {a[1]} {a[2]} right {b[1]} {b[2]}")
    left_sum = sum(int(row[1]) for row in left)
    right_sum = sum(int(row[1]) for row in right)
    print(f"positions {len(left)}")
    print(f"left_sum {left_sum}")
    print(f"right_sum {right_sum}")
    print(f"differ {differ} of {len(left)}")
    for line in first:
        print(line)


if __name__ == "__main__":
    main()
