#!/usr/bin/env python3
"""Compare two sum_nodes.py files. Prints equal and differ counts."""
import sys
from pathlib import Path


def rows(path: Path) -> list[int]:
    out = []
    for line in path.read_text().splitlines():
        parts = line.split()
        if len(parts) == 2 and parts[0].isdigit():
            out.append(int(parts[1]))
    return out


left = rows(Path(sys.argv[1]))
right = rows(Path(sys.argv[2]))
n = min(len(left), len(right))
differ = sum(1 for i in range(n) if left[i] != right[i])
print(f"left {sys.argv[1]} count {len(left)}")
print(f"right {sys.argv[2]} count {len(right)}")
print(f"compared {n}")
print(f"equal {n - differ}")
print(f"differ {differ}")
