#!/usr/bin/env python3
"""Compare per-position node counts from two depth_nodes.py raw logs."""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sum_nodes import blocks, nodes_of


def series(path: Path, depth: int) -> list[int | None]:
    return [nodes_of(block, depth) for block in blocks(path.read_text())]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--left", required=True)
    parser.add_argument("--right", required=True)
    parser.add_argument("--depth", type=int, required=True)
    parser.add_argument("--label", required=True)
    args = parser.parse_args()
    left = series(Path(args.left), args.depth)
    right = series(Path(args.right), args.depth)
    n = min(len(left), len(right))
    differ = 0
    missing = 0
    for index in range(n):
        if left[index] is None or right[index] is None:
            missing += 1
            continue
        if left[index] != right[index]:
            differ += 1
    print(f"label {args.label}")
    print(f"left {args.left}")
    print(f"right {args.right}")
    print(f"left_positions {len(left)}")
    print(f"right_positions {len(right)}")
    print(f"compared {n}")
    print(f"missing {missing}")
    print(f"differ {differ}")
    print(f"same {n - differ - missing}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
