#!/usr/bin/env python3
"""Compare two .nodes.txt files position by position."""
import sys
from pathlib import Path


def load(path: Path) -> list[int]:
    return [int(line) for line in path.read_text().splitlines() if line.strip()]


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: compare_nodes.py left.nodes.txt right.nodes.txt")
    left = load(Path(sys.argv[1]))
    right = load(Path(sys.argv[2]))
    if len(left) != len(right):
        print(f"length {len(left)} {len(right)}")
        raise SystemExit(1)
    differ = [i for i, (a, b) in enumerate(zip(left, right)) if a != b]
    print(f"positions {len(left)}")
    print(f"left_sum {sum(left)}")
    print(f"right_sum {sum(right)}")
    print(f"differ {len(differ)} of {len(left)}")
    for i in differ[:8]:
        print(f"pos {i + 1} left {left[i]} right {right[i]}")


if __name__ == "__main__":
    main()
