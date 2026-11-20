#!/usr/bin/env python3
"""Sum per-position node counts from a search_set.py raw log.

Prints: count, sum, then the first three node counts, then index and nodes.
"""
import re
import sys
from pathlib import Path

text = Path(sys.argv[1]).read_text(errors="replace").splitlines()
nodes_re = re.compile(r" nodes (\d+) ")
rows = []
current = None
last_nodes = None
for line in text:
    if line.startswith("# position "):
        current = int(line.split()[2])
        last_nodes = None
        continue
    if line.startswith("# endposition ") and current is not None:
        if last_nodes is None:
            raise SystemExit(f"no nodes for position {current}")
        rows.append((current, last_nodes))
        current = None
        continue
    match = nodes_re.search(line)
    if match and current is not None:
        last_nodes = int(match.group(1))
if not rows:
    raise SystemExit("no positions")
total = sum(n for _, n in rows)
print(f"count {len(rows)}")
print(f"sum {total}")
head = " ".join(str(n) for _, n in rows[:3])
print(f"first3 {head}")
for index, n in rows:
    print(f"{index} {n}")
