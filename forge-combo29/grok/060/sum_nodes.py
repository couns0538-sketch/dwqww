#!/usr/bin/env python3
"""Print count, sum, and the first three node counts of a search_set tsv."""
import sys

def main():
    path = sys.argv[1]
    nodes = []
    with open(path, encoding="utf-8") as handle:
        header = handle.readline().rstrip("\n").split("\t")
        column = header.index("nodes")
        depth_column = header.index("depth")
        for line in handle:
            parts = line.rstrip("\n").split("\t")
            nodes.append(int(parts[column]))
            if len(sys.argv) > 2 and int(parts[depth_column]) != int(sys.argv[2]):
                sys.stderr.write("depth mismatch " + parts[depth_column] + "\n")
    print("count", len(nodes))
    print("sum", sum(nodes))
    print("first", " ".join(str(n) for n in nodes[:3]))

if __name__ == "__main__":
    main()
