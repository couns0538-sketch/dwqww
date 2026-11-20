#!/usr/bin/env python3
"""Compare my depth_sum .nodes.txt to a partner row file.

My rows: index depth nodes
Partner rows: index nodes bestmove fen, separated by tabs.
"""
import sys
from pathlib import Path


def mine(path: Path) -> list[int]:
    nodes = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        _index, _depth, count = line.split()
        nodes.append(int(count))
    return nodes


def partner(path: Path) -> list[int]:
    nodes = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        if len(parts) < 2:
            parts = line.split()
        nodes.append(int(parts[1]))
    return nodes


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: compare_partner_rows.py <mine.nodes.txt> <partner.rows>", file=sys.stderr)
        return 2
    left = mine(Path(sys.argv[1]))
    right = partner(Path(sys.argv[2]))
    n = min(len(left), len(right))
    differ = 0
    first = None
    for index in range(n):
        if left[index] != right[index]:
            differ += 1
            if first is None:
                first = (index + 1, left[index], right[index])
    print(f"mine {sys.argv[1]} positions {len(left)}")
    print(f"partner {sys.argv[2]} positions {len(right)}")
    print(f"compared {n}")
    print(f"differ {differ}")
    print(f"equal {n - differ}")
    if len(left) != len(right):
        print(f"length_mismatch {len(left)} {len(right)}")
    if first is None:
        print("first_difference none")
    else:
        print(f"first_difference index {first[0]} mine {first[1]} partner {first[2]}")
    print(f"mine_sum {sum(left)}")
    print(f"partner_sum {sum(right)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
