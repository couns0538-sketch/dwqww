#!/usr/bin/env python3
"""Print position count, node sum, and the first three node counts of a tsv."""
import sys
from pathlib import Path

path = Path(sys.argv[1])
rows = []
for line in path.read_text().splitlines()[1:]:
    if not line.strip():
        continue
    index, nodes, move, fen = line.split("\t", 3)
    rows.append((int(index), int(nodes), move))
total = sum(nodes for _, nodes, _ in rows)
first = " ".join(str(nodes) for _, nodes, _ in rows[:3])
print(f"file {path.name}")
print(f"positions {len(rows)}")
print(f"sum {total}")
print(f"first3 {first}")
