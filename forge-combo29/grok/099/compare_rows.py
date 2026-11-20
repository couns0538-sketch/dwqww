#!/usr/bin/env python3
"""Compare node columns of two run_depth.py .rows.txt files."""
import sys
from pathlib import Path


def load(path: Path) -> list[tuple[int, str]]:
    rows = []
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        parts = line.split()
        rows.append((int(parts[1]), parts[2]))
    return rows


def main() -> int:
    a = load(Path(sys.argv[1]))
    b = load(Path(sys.argv[2]))
    n = min(len(a), len(b))
    differ = []
    for i in range(n):
        if a[i][0] != b[i][0]:
            differ.append(i)
    print(f"left {sys.argv[1]} n={len(a)}")
    print(f"right {sys.argv[2]} n={len(b)}")
    print(f"compared {n}")
    print(f"equal {n - len(differ)}")
    print(f"differ {len(differ)}")
    for i in differ[:12]:
        print(f"pos {i} left {a[i][0]} {a[i][1]} right {b[i][0]} {b[i][1]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
