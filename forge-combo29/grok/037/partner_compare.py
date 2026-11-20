#!/usr/bin/env python3
"""Compare node columns. Each row is index, nodes, then anything."""
import sys
from pathlib import Path


def nodes(path: Path):
    out = []
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        out.append(int(parts[1]))
    return out


def main() -> int:
    left = nodes(Path(sys.argv[1]))
    right = nodes(Path(sys.argv[2]))
    label = sys.argv[3]
    n = min(len(left), len(right))
    differ = sum(1 for i in range(n) if left[i] != right[i])
    print(f"label\t{label}")
    print(f"left_n\t{len(left)}")
    print(f"right_n\t{len(right)}")
    print(f"compared\t{n}")
    print(f"differ\t{differ}")
    return 0 if len(left) == len(right) else 1


if __name__ == "__main__":
    sys.exit(main())
