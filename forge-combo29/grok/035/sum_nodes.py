#!/usr/bin/env python3
"""Print node sums and the first three rows from measure_depth .nodes files."""
import sys
from pathlib import Path

def main():
    for path_s in sys.argv[1:]:
        path = Path(path_s)
        rows = []
        for line in path.read_text().splitlines():
            index, nodes, fen = line.split("\t", 2)
            rows.append((int(index), int(nodes), fen))
        total = sum(n for _, n, _ in rows)
        first = " ".join(str(n) for _, n, _ in rows[:3])
        print(f"{path.name}\tpositions\t{len(rows)}\tsum\t{total}\tfirst3\t{first}")

if __name__ == "__main__":
    main()
