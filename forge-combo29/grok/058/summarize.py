#!/usr/bin/env python3
"""Print sums and row differences from harness .rows files. Reads the files named on the command line."""
import sys


def load(path):
    rows = []
    with open(path, encoding="utf-8") as handle:
        next(handle)
        for line in handle:
            index, nodes, move = line.rstrip("\n").split("\t")
            rows.append((int(index), int(nodes), move))
    return rows


def main():
    if len(sys.argv) < 2:
        print("usage: summarize.py rows [rows ...]", file=sys.stderr)
        return 2
    loaded = [(path, load(path)) for path in sys.argv[1:]]
    print("file\tpositions\tsum\tfirst3")
    for path, rows in loaded:
        first = "/".join(str(nodes) for _, nodes, _ in rows[:3])
        print(f"{path}\t{len(rows)}\t{sum(nodes for _, nodes, _ in rows)}\t{first}")
    if len(loaded) >= 2 and len(loaded) % 2 == 0:
        for index in range(0, len(loaded), 2):
            left, right = loaded[index], loaded[index + 1]
            differ_nodes = 0
            differ_moves = 0
            for (_, nodes_a, move_a), (_, nodes_b, move_b) in zip(left[1], right[1]):
                if nodes_a != nodes_b:
                    differ_nodes += 1
                if move_a != move_b:
                    differ_moves += 1
            print(
                f"differ_nodes\t{differ_nodes}\tof\t{len(left[1])}\t"
                f"differ_moves\t{differ_moves}\t{left[0]}\t{right[0]}"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
