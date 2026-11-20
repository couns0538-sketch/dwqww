#!/usr/bin/env python3
"""Compare node columns of two .rows files. Prints equals, differs, and the first mismatches."""
import sys
from pathlib import Path

def load(path: Path) -> list[tuple[str, str, str]]:
    rows = []
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        index, nodes, fen = line.split(" ", 2)
        rows.append((index, nodes, fen))
    return rows

def main() -> int:
    if len(sys.argv) != 3:
        print("usage: compare_rows.py LEFT RIGHT", file=sys.stderr)
        return 2
    left = load(Path(sys.argv[1]))
    right = load(Path(sys.argv[2]))
    n = min(len(left), len(right))
    differ = 0
    shown = 0
    for i in range(n):
        if left[i][1] != right[i][1] or left[i][2] != right[i][2]:
            differ += 1
            if shown < 8:
                print(f"diff index {left[i][0]} left {left[i][1]} right {right[i][1]}")
                shown += 1
    length = "same_length" if len(left) == len(right) else f"length {len(left)} {len(right)}"
    print(f"compared {n} {length} differ {differ}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
