#!/usr/bin/env python3
"""Compare two suite_nodes row files. Prints equals, differs, and the first mismatches."""
import sys
from pathlib import Path


def load(path: Path) -> list[tuple[str, str, str]]:
    rows = []
    for line in path.read_text().splitlines():
        if line.startswith("SUM ") or not line.strip():
            continue
        index, nodes, depth, fen = line.split(None, 3)
        rows.append((index, nodes, fen))
    return rows


def main() -> int:
    left = load(Path(sys.argv[1]))
    right = load(Path(sys.argv[2]))
    if len(left) != len(right):
        print(f"length {len(left)} {len(right)}")
        return 1
    differ = 0
    shown = 0
    for a, b in zip(left, right):
        if a[2] != b[2]:
            print(f"fen mismatch at {a[0]}")
            return 1
        if a[1] != b[1]:
            differ += 1
            if shown < 12:
                print(f"diff {a[0]} {a[1]} {b[1]} {a[2]}")
                shown += 1
    print(f"positions {len(left)} differ {differ} equal {len(left) - differ}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
