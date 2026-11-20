#!/usr/bin/env python3
"""Compare our read_nodes table to a partner file with one node count per line."""
import sys
from pathlib import Path


def ours(path: Path) -> list[int]:
    rows = []
    for line in path.read_text().splitlines():
        parts = line.split("\t")
        if len(parts) < 3 or not parts[0].isdigit():
            continue
        rows.append(int(parts[2]))
    return rows


def claimed(path: Path) -> list[int]:
    rows = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if line.isdigit():
            rows.append(int(line))
    return rows


def main() -> int:
    left = ours(Path(sys.argv[1]))
    right = claimed(Path(sys.argv[2]))
    n = min(len(left), len(right))
    differ = 0
    print("index\tours\ttheirs")
    for i in range(n):
        if left[i] != right[i]:
            differ += 1
            print(f"{i + 1}\t{left[i]}\t{right[i]}")
    print(f"compared\t{n}")
    print(f"ours_rows\t{len(left)}")
    print(f"their_rows\t{len(right)}")
    print(f"differ\t{differ}")
    print(f"ours_sum\t{sum(left)}")
    print(f"their_sum\t{sum(right)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
