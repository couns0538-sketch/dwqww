#!/usr/bin/env python3
"""Compare two read_nodes.py tables. Prints how many positions differ."""
import sys
from pathlib import Path


def load(path: Path) -> list[tuple[str, str]]:
    rows = []
    for line in path.read_text().splitlines():
        if not line or line.startswith("index\t") or line.startswith("positions\t") or line.startswith("sum\t") or line.startswith("first3\t"):
            continue
        parts = line.split("\t")
        if len(parts) < 3:
            continue
        rows.append((parts[1], parts[2]))
    return rows


def main() -> int:
    left = load(Path(sys.argv[1]))
    right = load(Path(sys.argv[2]))
    n = min(len(left), len(right))
    differ = 0
    print("index\tleft_nodes\tright_nodes")
    for i in range(n):
        if left[i][1] != right[i][1]:
            differ += 1
            print(f"{i + 1}\t{left[i][1]}\t{right[i][1]}")
    print(f"compared\t{n}")
    print(f"left_rows\t{len(left)}")
    print(f"right_rows\t{len(right)}")
    print(f"differ\t{differ}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
