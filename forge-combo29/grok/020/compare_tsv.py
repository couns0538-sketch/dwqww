#!/usr/bin/env python3
"""Compare node columns of two measure_set tsv files."""
import sys
from pathlib import Path


def load(path: Path) -> list[tuple[str, int, str]]:
    rows = []
    for line in path.read_text().splitlines()[1:]:
        if not line.strip():
            continue
        parts = line.split("\t")
        rows.append((parts[0], int(parts[1]), parts[3]))
    return rows


def main() -> int:
    left = load(Path(sys.argv[1]))
    right = load(Path(sys.argv[2]))
    if len(left) != len(right):
        print(f"length {len(left)} {len(right)}")
        return 1
    differ = []
    for (i1, n1, m1), (i2, n2, m2) in zip(left, right):
        if n1 != n2 or m1 != m2:
            differ.append((i1, n1, n2, m1, m2))
    print(f"left {sys.argv[1]}")
    print(f"right {sys.argv[2]}")
    print(f"positions {len(left)}")
    print(f"left_sum {sum(n for _i, n, _m in left)}")
    print(f"right_sum {sum(n for _i, n, _m in right)}")
    print(f"differ {len(differ)}")
    for row in differ[:20]:
        print("row", " ".join(str(x) for x in row))
    if len(differ) > 20:
        print(f"more {len(differ) - 20}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
