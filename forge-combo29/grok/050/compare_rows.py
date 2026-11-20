#!/usr/bin/env python3
"""Compare two .rows files from depth_set.py. Prints counts, never a hand total."""
import sys
from pathlib import Path


def load(path):
    rows = {}
    summary = []
    for line in Path(path).read_text().splitlines():
        parts = line.split()
        if not parts:
            continue
        if parts[0] in {"sum", "first3"}:
            summary.append(line)
            continue
        rows[int(parts[0])] = (int(parts[1]), int(parts[2]))
    return rows, summary


def main():
    if len(sys.argv) != 3:
        sys.exit("usage: compare_rows.py LEFT.rows RIGHT.rows")
    left, left_sum = load(sys.argv[1])
    right, right_sum = load(sys.argv[2])
    keys = sorted(set(left) | set(right))
    differ = 0
    missing = 0
    for key in keys:
        if key not in left or key not in right:
            missing += 1
            continue
        if left[key][0] != right[key][0]:
            differ += 1
    print(f"left {sys.argv[1]}")
    print(f"right {sys.argv[2]}")
    print(f"positions {len(keys)}")
    print(f"missing {missing}")
    print(f"differ {differ}")
    print(f"same {len(keys) - missing - differ}")
    for line in left_sum:
        print(f"left {line}")
    for line in right_sum:
        print(f"right {line}")


if __name__ == "__main__":
    main()
