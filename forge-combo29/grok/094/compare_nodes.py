#!/usr/bin/env python3
"""Compare two node files written by measure_depth.py. Prints the script's own count."""

import argparse
from pathlib import Path


def load(path: Path) -> list[int]:
    rows = []
    for line in path.read_text().splitlines():
        text = line.strip()
        if text:
            rows.append(int(text))
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("left")
    parser.add_argument("right")
    args = parser.parse_args()
    left = load(Path(args.left))
    right = load(Path(args.right))
    n = min(len(left), len(right))
    differ = [i for i in range(n) if left[i] != right[i]]
    print(f"left {args.left} rows {len(left)} sum {sum(left)}")
    print(f"right {args.right} rows {len(right)} sum {sum(right)}")
    print(f"compared {n}")
    print(f"differ {len(differ)}")
    for index in differ[:20]:
        print(f"row {index} left {left[index]} right {right[index]}")
    if len(left) != len(right):
        print(f"length mismatch {len(left)} {len(right)}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
