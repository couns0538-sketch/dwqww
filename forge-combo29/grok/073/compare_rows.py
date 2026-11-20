#!/usr/bin/env python3
"""Compare two harness row files. Prints counts from the files, never typed numbers."""

import sys


def load(path):
    rows = []
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            if line.startswith("#") or not line.strip():
                continue
            parts = line.split()
            rows.append((int(parts[0]), int(parts[1]), parts[2]))
    return rows


def main():
    left = load(sys.argv[1])
    right = load(sys.argv[2])
    if len(left) != len(right):
        print(f"length {len(left)} {len(right)}")
        return 1
    differ = 0
    move_differ = 0
    for (i, nodes, move), (j, nodes2, move2) in zip(left, right):
        if i != j:
            print("index mismatch", i, j)
            return 1
        if nodes != nodes2:
            differ += 1
        if move != move2:
            move_differ += 1
    print(f"count {len(left)}")
    print(f"sum_left {sum(item[1] for item in left)}")
    print(f"sum_right {sum(item[1] for item in right)}")
    print(f"nodes_differ {differ} of {len(left)}")
    print(f"move_differ {move_differ} of {len(left)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
