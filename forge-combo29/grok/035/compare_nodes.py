#!/usr/bin/env python3
"""Compare two .nodes files position by position. Prints differ count and the sum."""
import sys
from pathlib import Path

def load(path: Path):
    rows = []
    for line in path.read_text().splitlines():
        index, nodes, fen = line.split("\t", 2)
        rows.append((int(index), int(nodes), fen))
    return rows

def main():
    left = load(Path(sys.argv[1]))
    right = load(Path(sys.argv[2]))
    if len(left) != len(right):
        raise SystemExit(f"length {len(left)} vs {len(right)}")
    differ = 0
    for (i, a, fa), (j, b, fb) in zip(left, right):
        if i != j or fa != fb:
            raise SystemExit(f"row mismatch {i} {j}")
        if a != b:
            differ += 1
    print(f"left {sys.argv[1]} sum {sum(n for _, n, _ in left)}")
    print(f"right {sys.argv[2]} sum {sum(n for _, n, _ in right)}")
    print(f"positions {len(left)}")
    print(f"differ {differ}")
    print(f"same {len(left) - differ}")

if __name__ == "__main__":
    main()
