#!/usr/bin/env python3
"""Compare my .nodes file with a partner rows file of 'index nodes fen'."""
import sys
from pathlib import Path


def mine(path: Path) -> list[tuple[int, int]]:
    rows = []
    for line in path.read_text().splitlines():
        if line.startswith("sum ") or line.startswith("count "):
            continue
        index, nodes = line.split()[:2]
        rows.append((int(index), int(nodes)))
    return rows


def partner(path: Path) -> list[tuple[int, int]]:
    rows = []
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        index, nodes = line.split()[:2]
        rows.append((int(index), int(nodes)))
    return rows


def main() -> int:
    left = mine(Path(sys.argv[1]))
    right = partner(Path(sys.argv[2]))
    print(f"mine {len(left)} partner {len(right)}")
    if len(left) != len(right):
        return 2
    differ = 0
    shown = 0
    for (i1, n1), (i2, n2) in zip(left, right):
        if i1 != i2:
            print(f"index {i1} vs {i2}")
            return 2
        if n1 != n2:
            differ += 1
            if shown < 5:
                print(f"diff {i1} mine {n1} partner {n2}")
                shown += 1
    print(f"differ {differ}")
    print(f"same {len(left) - differ}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
