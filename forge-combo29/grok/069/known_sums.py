#!/usr/bin/env python3
"""Print node sums and the first rows of a harness TSV. Usage: known_sums.py FILE [expected_sum]"""
import sys
from pathlib import Path

path = Path(sys.argv[1])
expected = int(sys.argv[2]) if len(sys.argv) > 2 else None
rows = []
for line in path.read_text().splitlines()[1:]:
    if not line.strip():
        continue
    idx, nodes, best, fen, info = line.split("\t", 4)
    rows.append((int(idx), int(nodes), best))
total = sum(nodes for _, nodes, _ in rows)
print(f"file\t{path.name}")
print(f"positions\t{len(rows)}")
print(f"nodes_sum\t{total}")
if expected is not None:
    print(f"expected\t{expected}")
    print(f"match\t{'yes' if total == expected else 'no'}")
print("first3")
for idx, nodes, best in rows[:3]:
    print(f"{idx}\t{nodes}\t{best}")
