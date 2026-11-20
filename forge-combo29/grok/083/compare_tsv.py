#!/usr/bin/env python3
"""Position-by-position node compare. Prints how many rows differ."""
import sys
from pathlib import Path


def load(path: Path):
    rows = []
    for line in path.read_text().splitlines()[1:]:
        if not line.strip():
            continue
        index, nodes, score, fen = line.split("\t", 3)
        rows.append((int(index), int(nodes), fen))
    return rows


def main() -> None:
    left = load(Path(sys.argv[1]))
    right = load(Path(sys.argv[2]))
    if len(left) != len(right):
        raise SystemExit(f"length {len(left)} != {len(right)}")
    differ = []
    for (i, a, fen_a), (j, b, fen_b) in zip(left, right):
        if i != j or fen_a != fen_b:
            raise SystemExit(f"row mismatch {i} {j}")
        if a != b:
            differ.append((i, a, b))
    print(f"left {sys.argv[1]}")
    print(f"right {sys.argv[2]}")
    print(f"positions {len(left)}")
    print(f"differ {len(differ)}")
    print(f"same {len(left) - len(differ)}")
    for i, a, b in differ[:20]:
        print(f"pos {i} {a} {b}")
    if len(differ) > 20:
        print(f"... {len(differ) - 20} more")


if __name__ == "__main__":
    main()
