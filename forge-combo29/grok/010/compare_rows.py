#!/usr/bin/env python3
"""Compare two measure_depth .rows files. Prints how many positions differ."""
import sys

def load(path):
    rows = []
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            parts = line.rstrip("\n").split("\t")
            if len(parts) < 2:
                continue
            rows.append((int(parts[0]), int(parts[1]), parts[2] if len(parts) > 2 else ""))
    return rows

def main():
    left = load(sys.argv[1])
    right = load(sys.argv[2])
    n = min(len(left), len(right))
    differ = 0
    first = []
    for i in range(n):
        if left[i][1] != right[i][1]:
            differ += 1
            if len(first) < 5:
                first.append("%d %d %d" % (i, left[i][1], right[i][1]))
    print("left %d right %d compared %d differ %d" % (len(left), len(right), n, differ))
    for line in first:
        print("example " + line)
    if len(left) != len(right):
        print("FAIL length")
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())
