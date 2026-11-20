#!/usr/bin/env python3
"""Compare the node column of two files. A line is index, nodes, then anything.
Lines whose second field is not an integer are ignored (SUM, COUNT).
"""
import sys
from pathlib import Path


def load(path: Path) -> list[int]:
    rows = []
    for line in path.read_text().splitlines():
        parts = line.split()
        if len(parts) < 2:
            continue
        try:
            int(parts[0])
            rows.append(int(parts[1]))
        except ValueError:
            continue
    return rows


def main() -> int:
    a = load(Path(sys.argv[1]))
    b = load(Path(sys.argv[2]))
    n = min(len(a), len(b))
    differ = [i for i in range(n) if a[i] != b[i]]
    print(f"left {sys.argv[1]} n={len(a)} sum={sum(a)}")
    print(f"right {sys.argv[2]} n={len(b)} sum={sum(b)}")
    print(f"compared {n}")
    print(f"equal {n - len(differ)}")
    print(f"differ {len(differ)}")
    for i in differ[:8]:
        print(f"pos {i} left {a[i]} right {b[i]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
