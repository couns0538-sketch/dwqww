#!/usr/bin/env python3
"""Compare my .nodes file with seat 089's tab-separated rows."""
import sys
from pathlib import Path

mine = [int(line) for line in Path(sys.argv[1]).read_text().splitlines() if line.strip()]
theirs = []
for line in Path(sys.argv[2]).read_text().splitlines():
    if not line.strip():
        continue
    index, nodes, _rest = line.split("\t", 2)
    theirs.append((int(index), int(nodes)))
if len(mine) != len(theirs):
    print(f"length {len(mine)} {len(theirs)}")
    sys.exit(1)
differ = 0
for i, ((index, nodes), mine_nodes) in enumerate(zip(theirs, mine), start=1):
    if index != i or nodes != mine_nodes:
        differ += 1
        if differ <= 8:
            print(f"pos {i} mine {mine_nodes} partner {nodes} index {index}")
print(f"positions {len(mine)}")
print(f"differ {differ}")
print(f"equal {len(mine) - differ}")
print(f"sum_mine {sum(mine)}")
print(f"sum_partner {sum(n for _, n in theirs)}")
