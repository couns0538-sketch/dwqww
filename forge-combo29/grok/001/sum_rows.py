#!/usr/bin/env python3
"""Sum node counts from a depth_set rows file. Prints the sum and the first three nodes."""
import sys
from pathlib import Path

path = Path(sys.argv[1])
nodes = []
for line in path.read_text().splitlines():
    if not line.strip():
        continue
    parts = line.split()
    nodes.append(int(parts[1]))
print(f"file={path}")
print(f"positions={len(nodes)}")
print(f"sum={sum(nodes)}")
if nodes:
    shown = " / ".join(str(n) for n in nodes[:3])
    print(f"first3={shown}")
