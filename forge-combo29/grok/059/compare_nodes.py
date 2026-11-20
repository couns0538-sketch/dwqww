#!/usr/bin/env python3
"""Compare two .nodes files produced by search_set.py. Prints the difference count."""
import sys
from pathlib import Path


def load(path: Path) -> list[int]:
    rows = []
    for line in path.read_text().splitlines():
        if line.startswith("sum ") or line.startswith("count "):
            continue
        index, nodes = line.split()
        rows.append((int(index), int(nodes)))
    return rows


def main() -> int:
    left = load(Path(sys.argv[1]))
    right = load(Path(sys.argv[2]))
    if len(left) != len(right):
        print(f"count {len(left)} vs {len(right)}")
        return 2
    differ = 0
    first = []
    for (i1, n1), (i2, n2) in zip(left, right):
        if i1 != i2:
            print(f"index {i1} vs {i2}")
            return 2
        if n1 != n2:
            differ += 1
            if len(first) < 5:
                first.append(f"{i1} {n1} {n2}")
    print(f"positions {len(left)}")
    print(f"differ {differ}")
    print(f"same {len(left) - differ}")
    for line in first:
        print(f"example {line}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
