#!/usr/bin/env python3
"""Compare my depth-12 raw log with the partner's index/nodes/fen rows."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sum_nodes import blocks, nodes_of

raw = Path(sys.argv[1])
theirs = Path(sys.argv[2])
depth = int(sys.argv[3])
mine = [nodes_of(block, depth) for block in blocks(raw.read_text())]
rows = []
for line in theirs.read_text().splitlines():
    if not line.strip():
        continue
    index, nodes, fen = line.split("\t", 2)
    rows.append((int(index), int(nodes), fen))
differ = 0
missing = 0
for index, nodes, _fen in rows:
    got = mine[index - 1] if 0 < index <= len(mine) else None
    if got is None:
        missing += 1
    elif got != nodes:
        differ += 1
print(f"partner_rows {len(rows)}")
print(f"mine {len(mine)}")
print(f"differ {differ}")
print(f"missing {missing}")
print(f"same {len(rows) - differ - missing}")
