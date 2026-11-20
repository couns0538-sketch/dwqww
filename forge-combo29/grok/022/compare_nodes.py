#!/usr/bin/env python3
"""Compare two node lists written by parse_nodes.py. Prints equals and the differ count."""
import sys
from pathlib import Path


def load(path: Path) -> list[int]:
    return [int(line) for line in path.read_text().splitlines() if line.strip()]


def main() -> int:
    left = load(Path(sys.argv[1]))
    right = load(Path(sys.argv[2]))
    if len(left) != len(right):
        print(f"length {len(left)} {len(right)}")
        return 1
    differ = sum(1 for a, b in zip(left, right) if a != b)
    print(f"positions {len(left)}")
    print(f"differ {differ}")
    print(f"equal {differ == 0}")
    print(f"sum_left {sum(left)}")
    print(f"sum_right {sum(right)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
