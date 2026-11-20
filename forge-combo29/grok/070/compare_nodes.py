#!/usr/bin/env python3
"""Compare two sum_nodes.py listings. Prints how many rows differ."""
import sys


def rows(path):
    out = []
    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            parts = line.split()
            if len(parts) == 2 and parts[0].isdigit():
                out.append(int(parts[1]))
    return out


def main():
    left = rows(sys.argv[1])
    right = rows(sys.argv[2])
    if len(left) != len(right):
        print(f"length {len(left)} {len(right)}")
        raise SystemExit(2)
    differ = [i for i, (a, b) in enumerate(zip(left, right), start=1) if a != b]
    print(f"positions {len(left)}")
    print(f"differ {len(differ)}")
    print(f"sum_left {sum(left)}")
    print(f"sum_right {sum(right)}")
    for i in differ[:20]:
        print(f"{i} {left[i - 1]} {right[i - 1]}")


if __name__ == "__main__":
    main()
