#!/usr/bin/env python3
"""Print node sum and the first three node counts from a rows file."""
import sys
from pathlib import Path

path = Path(sys.argv[1])
nodes = []
for line in path.read_text().splitlines():
    if not line.strip():
        continue
    nodes.append(int(line.split("\t")[1]))
print(f"positions {len(nodes)}")
print(f"sum {sum(nodes)}")
if len(nodes) >= 3:
    print(f"first3 {nodes[0]} {nodes[1]} {nodes[2]}")
