#!/usr/bin/env python3
"""Compare my 4-column rows to the partner's 3-column index, nodes, fen file."""
import sys

def mine(path):
    rows = []
    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            index, nodes, _best, fen = line.rstrip("\n").split("\t", 3)
            rows.append((int(index), int(nodes), fen))
    return rows

def theirs(path):
    rows = []
    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            index, nodes, fen = line.rstrip("\n").split("\t", 2)
            rows.append((int(index), int(nodes), fen))
    return rows

def main():
    left = mine(sys.argv[1])
    right = theirs(sys.argv[2])
    n = min(len(left), len(right))
    differ = 0
    examples = []
    for i in range(n):
        if left[i][1] != right[i][1] or left[i][2] != right[i][2]:
            differ += 1
            if len(examples) < 5:
                examples.append((left[i][0], left[i][1], right[i][1]))
    print(f"mine {sys.argv[1]}")
    print(f"partner {sys.argv[2]}")
    print(f"mine_rows {len(left)}")
    print(f"partner_rows {len(right)}")
    print(f"compared {n}")
    print(f"differ {differ}")
    for index, a, b in examples:
        print(f"example {index} {a} {b}")

if __name__ == "__main__":
    main()
