#!/usr/bin/env python3
"""Print a node-sum table from measure_set.py .rows files. Numbers come only from those files."""
import sys

def load(path):
    rows = []
    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            index, nodes, best, fen = line.rstrip("\n").split("\t", 3)
            rows.append((int(index), int(nodes), best, fen))
    return rows

def main():
    if len(sys.argv) < 2:
        sys.stderr.write("usage: sum_rows.py ROWS [ROWS ...]\n")
        sys.exit(2)
    for path in sys.argv[1:]:
        rows = load(path)
        total = sum(nodes for _, nodes, _, _ in rows)
        sys.stdout.write(f"file {path}\n")
        sys.stdout.write(f"positions {len(rows)}\n")
        sys.stdout.write(f"sum {total}\n")
        for index, nodes, best, _fen in rows[:3]:
            sys.stdout.write(f"first{index} {nodes} {best}\n")

if __name__ == "__main__":
    main()
