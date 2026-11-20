#!/usr/bin/env python3
"""Print sum, length, and first three node counts, or a position-by-position compare."""
import sys


def load(path):
    rows = []
    with open(path, encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            index, nodes, *_ = line.split("\t")
            rows.append((int(index), int(nodes)))
    return rows


def main():
    if len(sys.argv) == 2:
        rows = load(sys.argv[1])
        print(f"n {len(rows)}")
        print(f"sum {sum(nodes for _, nodes in rows)}")
        print("first3 " + " ".join(str(nodes) for _, nodes in rows[:3]))
        return
    left = load(sys.argv[1])
    right = load(sys.argv[2])
    if len(left) != len(right):
        raise SystemExit(f"length {len(left)} != {len(right)}")
    differ = [index for (index, a), (_, b) in zip(left, right) if a != b]
    print(f"n {len(left)}")
    print(f"differ {len(differ)}")
    if differ:
        print("first_differ " + " ".join(str(index) for index in differ[:10]))


if __name__ == "__main__":
    main()
