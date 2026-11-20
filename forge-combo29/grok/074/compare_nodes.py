#!/usr/bin/env python3
"""Compare two .nodes.txt files position by position. Prints the counts."""

import sys


def load(path):
    rows = []
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            parts = line.split()
            rows.append(int(parts[1]))
    return rows


def main():
    left = load(sys.argv[1])
    right = load(sys.argv[2])
    if len(left) != len(right):
        print(f"length {len(left)} {len(right)}")
        sys.exit(1)
    differ = sum(1 for a, b in zip(left, right) if a != b)
    print(f"n {len(left)} differ {differ} sum_left {sum(left)} sum_right {sum(right)}")
    if differ:
        shown = 0
        for index, (a, b) in enumerate(zip(left, right), start=1):
            if a != b:
                print(f"pos {index} {a} {b}")
                shown += 1
                if shown >= 8:
                    break


if __name__ == "__main__":
    main()
