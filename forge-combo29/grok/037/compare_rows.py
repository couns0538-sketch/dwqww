#!/usr/bin/env python3
"""Compare two node TSV files position by position. Prints a one-row table."""
import sys
from pathlib import Path


def load(path: Path):
    rows = []
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        index, nodes, fen = line.split("\t", 2)
        rows.append((int(index), int(nodes), fen))
    return rows


def main() -> int:
    left = load(Path(sys.argv[1]))
    right = load(Path(sys.argv[2]))
    label = sys.argv[3] if len(sys.argv) > 3 else "compare"
    if len(left) != len(right):
        print(f"{label} length {len(left)} vs {len(right)}")
        return 1
    differ = []
    for (i, a, fen), (_, b, fen_b) in zip(left, right):
        if fen != fen_b or a != b:
            differ.append((i, a, b))
    print("step\tdiffer\tn\tsame")
    print(f"{label}\t{len(differ)}\t{len(left)}\t{len(left) - len(differ)}")
    for i, a, b in differ[:20]:
        print(f"pos\t{i}\t{a}\t{b}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
