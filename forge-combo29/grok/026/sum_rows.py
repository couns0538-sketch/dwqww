#!/usr/bin/env python3
"""Sum node counts from a .rows file written by uci_harness.py. Prints the file's own numbers."""

import sys
from pathlib import Path

path = Path(sys.argv[1])
rows = []
for line in path.read_text(encoding="utf-8").splitlines():
    if not line.strip():
        continue
    parts = line.split()
    rows.append((int(parts[0]), int(parts[1]), " ".join(parts[2:])))
total = sum(nodes for _, nodes, _ in rows)
print(f"file {path}")
print(f"count {len(rows)}")
print(f"sum {total}")
for index, nodes, rest in rows[:3]:
    print(f"first {index} {nodes} {rest}")
