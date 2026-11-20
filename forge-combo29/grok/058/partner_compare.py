#!/usr/bin/env python3
"""Compare a harness .rows file with a partner nodes file (one integer per line)."""
import sys


def rows(path):
    values = []
    with open(path, encoding="utf-8") as handle:
        next(handle)
        for line in handle:
            index, nodes, move = line.rstrip("\n").split("\t")
            values.append(int(nodes))
    return values


def plain(path):
    values = []
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            text = line.strip()
            if text:
                values.append(int(text))
    return values


def main():
    left_path, right_path, kind = sys.argv[1:4]
    left = rows(left_path) if kind == "rows" else plain(left_path)
    right = rows(right_path) if sys.argv[4] == "rows" else plain(right_path)
    differ = sum(a != b for a, b in zip(left, right))
    print(f"n\t{len(left)}\t{len(right)}")
    print(f"sum_left\t{sum(left)}")
    print(f"sum_right\t{sum(right)}")
    print(f"differ\t{differ}\tof\t{min(len(left), len(right))}")
    print(f"left\t{left_path}")
    print(f"right\t{right_path}")


if __name__ == "__main__":
    raise SystemExit(main())
