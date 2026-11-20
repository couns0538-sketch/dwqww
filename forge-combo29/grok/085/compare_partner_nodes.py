#!/usr/bin/env python3
"""Compare my nodes file with a partner file (spaces or tabs)."""
import sys
from pathlib import Path


def load(path: Path) -> list[tuple[str, int, str]]:
    rows = []
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        if "\t" in line:
            index, nodes, fen = line.split("\t", 2)
        else:
            index, nodes, fen = line.split(" ", 2)
        rows.append((index, int(nodes), fen))
    return rows


def main() -> int:
    left = load(Path(sys.argv[1]))
    right = load(Path(sys.argv[2]))
    print(f"left {sys.argv[1]} n {len(left)} sum {sum(n for _, n, _ in left)}")
    print(f"right {sys.argv[2]} n {len(right)} sum {sum(n for _, n, _ in right)}")
    if len(left) != len(right):
        print("length differs")
        return 1
    differ = 0
    fen_mismatch = 0
    for (i1, n1, f1), (i2, n2, f2) in zip(left, right):
        if i1 != i2 or f1 != f2:
            fen_mismatch += 1
        if n1 != n2:
            differ += 1
    print(f"positions {len(left)}")
    print(f"fen_or_index_mismatch {fen_mismatch}")
    print(f"node_differ {differ}")
    print(f"node_equal {len(left) - differ}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
