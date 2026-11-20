#!/usr/bin/env python3
"""Compare two nodes files from search_depth.py. Prints equal count and differences."""
import sys
from pathlib import Path


def load(path: Path) -> list[tuple[str, int, str]]:
    rows = []
    for line in path.read_text().splitlines():
        index, nodes, fen = line.split(" ", 2)
        rows.append((index, int(nodes), fen))
    return rows


def main() -> int:
    left = load(Path(sys.argv[1]))
    right = load(Path(sys.argv[2]))
    if len(left) != len(right):
        print(f"length {len(left)} {len(right)}")
        return 1
    differ = []
    for (i1, n1, f1), (i2, n2, f2) in zip(left, right):
        if i1 != i2 or f1 != f2:
            print(f"row mismatch {i1} {i2}")
            return 1
        if n1 != n2:
            differ.append((i1, n1, n2))
    print(f"positions {len(left)}")
    print(f"equal {len(left) - len(differ)}")
    print(f"differ {len(differ)}")
    for index, n1, n2 in differ[:20]:
        print(f"pos {index} {n1} {n2}")
    if len(differ) > 20:
        print(f"... {len(differ) - 20} more")
    return 0


if __name__ == "__main__":
    sys.exit(main())
