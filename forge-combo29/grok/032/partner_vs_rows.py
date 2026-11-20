#!/usr/bin/env python3
"""Compare a partner row file to my depth_set .nodes file, in position order.

Partner rows are 'index nodes', then optional SUM and FIRST3 lines.
My rows are 'index nodes depth N' and are 1-based. Order is the comparison.
"""
import sys
from pathlib import Path


def partner_nodes(path: Path):
    rows = []
    for line in path.read_text().splitlines():
        parts = line.split()
        if len(parts) == 2 and parts[0].isdigit():
            rows.append(int(parts[1]))
    return rows


def mine_nodes(path: Path):
    rows = []
    for line in path.read_text().splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[0].isdigit():
            rows.append(int(parts[1]))
    return rows


def main() -> None:
    left = partner_nodes(Path(sys.argv[1]))
    right = mine_nodes(Path(sys.argv[2]))
    n = min(len(left), len(right))
    differ = sum(1 for a, b in zip(left, right) if a != b)
    print(f"partner_file {sys.argv[1]}")
    print(f"mine_file {sys.argv[2]}")
    print(f"partner_positions {len(left)}")
    print(f"mine_positions {len(right)}")
    print(f"compared {n}")
    print(f"same {n - differ}")
    print(f"differ {differ}")
    print(f"partner_sum {sum(left)}")
    print(f"mine_sum {sum(right)}")
    if len(left) != len(right):
        raise SystemExit("length mismatch")


if __name__ == "__main__":
    main()
