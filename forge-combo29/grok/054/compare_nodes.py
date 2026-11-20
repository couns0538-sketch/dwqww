#!/usr/bin/env python3
"""Compare two .nodes files written by search_set.py. Prints the difference count."""

import sys
from pathlib import Path


def load(path: Path) -> list[int]:
    return [int(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: compare_nodes.py left.nodes right.nodes", file=sys.stderr)
        return 2
    left = load(Path(sys.argv[1]))
    right = load(Path(sys.argv[2]))
    if len(left) != len(right):
        print(f"length {len(left)} {len(right)}")
        return 1
    differ = [i for i, (a, b) in enumerate(zip(left, right), start=1) if a != b]
    print(f"positions {len(left)}")
    print(f"left_sum {sum(left)}")
    print(f"right_sum {sum(right)}")
    print(f"differ {len(differ)} of {len(left)}")
    if differ[:12]:
        print("first_diffs " + " ".join(str(i) for i in differ[:12]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
