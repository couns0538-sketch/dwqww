#!/usr/bin/env python3
"""Compare two .rows files position by position. Prints only numbers read from the files."""
import sys

def load(path):
    rows = []
    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            index, nodes, best, fen = line.rstrip("\n").split("\t", 3)
            rows.append((int(index), int(nodes), best, fen))
    return rows

def main():
    left = load(sys.argv[1])
    right = load(sys.argv[2])
    n = min(len(left), len(right))
    differ = 0
    first = []
    for i in range(n):
        if left[i][1] != right[i][1] or left[i][3] != right[i][3]:
            differ += 1
            if len(first) < 5:
                first.append((left[i][0], left[i][1], right[i][1]))
    sys.stdout.write(f"left {sys.argv[1]}\n")
    sys.stdout.write(f"right {sys.argv[2]}\n")
    sys.stdout.write(f"left_rows {len(left)}\n")
    sys.stdout.write(f"right_rows {len(right)}\n")
    sys.stdout.write(f"compared {n}\n")
    sys.stdout.write(f"differ {differ}\n")
    for index, a, b in first:
        sys.stdout.write(f"example {index} {a} {b}\n")

if __name__ == "__main__":
    main()
