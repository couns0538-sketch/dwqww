#!/usr/bin/env python3
"""Compare two .nodes files written by depth_set.py. Prints one table."""
import sys
from pathlib import Path


def load(path: Path):
    rows = []
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        parts = line.split()
        rows.append((int(parts[0]), int(parts[1]), int(parts[3])))
    return rows


def main() -> None:
    left = load(Path(sys.argv[1]))
    right = load(Path(sys.argv[2]))
    if len(left) != len(right):
        raise SystemExit(f"length {len(left)} vs {len(right)}")
    differ = 0
    depth_mismatch = 0
    for (i, a, da), (j, b, db) in zip(left, right):
        if i != j:
            raise SystemExit(f"index {i} vs {j}")
        if a != b:
            differ += 1
        if da != db or da != int(sys.argv[3]):
            depth_mismatch += 1
    same = len(left) - differ
    print(f"file_a {sys.argv[1]}")
    print(f"file_b {sys.argv[2]}")
    print(f"positions {len(left)}")
    print(f"same {same}")
    print(f"differ {differ}")
    print(f"depth_not_{sys.argv[3]} {depth_mismatch}")
    print(f"sum_a {sum(n for _i, n, _d in left)}")
    print(f"sum_b {sum(n for _i, n, _d in right)}")


if __name__ == "__main__":
    main()
