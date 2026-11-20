#!/usr/bin/env python3
"""Compare two .rows files. Prints how many positions differ."""

import sys


def load(path: str) -> list[tuple[str, str, str]]:
    rows = []
    for line in open(path, encoding="utf-8"):
        index, nodes, move = line.split()
        rows.append((index, nodes, move))
    return rows


def main() -> None:
    left = load(sys.argv[1])
    right = load(sys.argv[2])
    if len(left) != len(right):
        raise SystemExit(f"length {len(left)} != {len(right)}")
    differ = 0
    for a, b in zip(left, right):
        if a != b:
            differ += 1
            if differ <= 8:
                print(f"differ {a[0]} left {a[1]} {a[2]} right {b[1]} {b[2]}")
    print(f"positions {len(left)}")
    print(f"differ {differ}")
    print(f"same {len(left) - differ}")


if __name__ == "__main__":
    main()
