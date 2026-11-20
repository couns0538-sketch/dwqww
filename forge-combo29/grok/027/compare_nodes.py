#!/usr/bin/env python3
"""Compare two .nodes files position by position. Prints a table row."""
import sys
from pathlib import Path


def load(path: Path) -> list[tuple[str, str, str]]:
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        rows.append((parts[0], parts[1], parts[2]))
    return rows


def main() -> int:
    left = load(Path(sys.argv[1]))
    right = load(Path(sys.argv[2]))
    name = sys.argv[3] if len(sys.argv) > 3 else "compare"
    n = min(len(left), len(right))
    differ = 0
    for i in range(n):
        if left[i][1] != right[i][1] or left[i][2] != right[i][2]:
            differ += 1
    sum_l = sum(int(row[1]) for row in left)
    sum_r = sum(int(row[1]) for row in right)
    print(f"name={name}")
    print(f"left={sys.argv[1]} n={len(left)} sum={sum_l}")
    print(f"right={sys.argv[2]} n={len(right)} sum={sum_r}")
    print(f"compared={n}")
    print(f"differ={differ}")
    print(f"same_length={str(len(left) == len(right)).lower()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
