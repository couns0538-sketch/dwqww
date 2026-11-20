#!/usr/bin/env python3
"""Compare two search_set tsv files position by position.

Prints equal or the number of positions whose node count differs,
and the first five differing indexes.
"""
import sys


def load(path):
    rows = []
    with open(path, encoding="utf-8") as handle:
        header = handle.readline().rstrip("\n").split("\t")
        column = header.index("nodes")
        for line in handle:
            parts = line.rstrip("\n").split("\t")
            rows.append(int(parts[column]))
    return rows


def main():
    left = load(sys.argv[1])
    right = load(sys.argv[2])
    print("left", len(left))
    print("right", len(right))
    n = min(len(left), len(right))
    differ = [i + 1 for i in range(n) if left[i] != right[i]]
    if len(left) != len(right):
        print("length_differs")
    print("differ", len(differ), "of", n)
    print("first_diff", " ".join(str(i) for i in differ[:5]))


if __name__ == "__main__":
    main()
