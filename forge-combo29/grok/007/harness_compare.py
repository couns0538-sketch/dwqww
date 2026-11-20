#!/usr/bin/env python3
"""Compare two rows files position by position."""
import sys
from pathlib import Path


def load(path: Path) -> list[tuple[str, str, str]]:
    rows = []
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        index, nodes, move = line.split("\t")
        rows.append((index, nodes, move))
    return rows


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: harness_compare.py LEFT.rows.tsv RIGHT.rows.tsv", file=sys.stderr)
        return 2
    left = load(Path(sys.argv[1]))
    right = load(Path(sys.argv[2]))
    if len(left) != len(right):
        print(f"length {len(left)} {len(right)}")
        return 1
    differ = 0
    for a, b in zip(left, right):
        if a[1] != b[1] or a[2] != b[2]:
            differ += 1
    print(f"positions {len(left)} differ {differ} equal {len(left) - differ}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
