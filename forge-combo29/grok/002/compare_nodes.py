#!/usr/bin/env python3
"""Compare two .nodes.txt files position by position.

Each row is: index depth nodes
Prints how many positions differ and the first difference.
"""
import sys
from pathlib import Path


def load(path: Path) -> list[tuple[int, int, int]]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        index, depth, nodes = line.split()
        rows.append((int(index), int(depth), int(nodes)))
    return rows


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: compare_nodes.py <a.nodes.txt> <b.nodes.txt>", file=sys.stderr)
        return 2
    left = load(Path(sys.argv[1]))
    right = load(Path(sys.argv[2]))
    print(f"left {sys.argv[1]} positions {len(left)}")
    print(f"right {sys.argv[2]} positions {len(right)}")
    n = min(len(left), len(right))
    differ = 0
    first = None
    for index in range(n):
        if left[index][2] != right[index][2] or left[index][0] != right[index][0]:
            differ += 1
            if first is None:
                first = (left[index], right[index])
    print(f"compared {n}")
    print(f"differ {differ}")
    print(f"equal {n - differ}")
    if len(left) != len(right):
        print(f"length_mismatch {len(left)} {len(right)}")
    if first is None:
        print("first_difference none")
    else:
        print(f"first_difference left {first[0][0]} {first[0][1]} {first[0][2]} right {first[1][0]} {first[1][1]} {first[1][2]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
