#!/usr/bin/env python3
"""Compare my .nodes file with seat 006's TSV (header, 1-based index, nodes, depth, fen)."""
import sys
from pathlib import Path

mine = [int(line) for line in Path(sys.argv[1]).read_text().splitlines() if line.strip()]
theirs = []
for line in Path(sys.argv[2]).read_text().splitlines()[1:]:
    if not line.strip():
        continue
    parts = line.split("\t")
    theirs.append(int(parts[1]))
n = min(len(mine), len(theirs))
differ = [i for i in range(n) if mine[i] != theirs[i]]
print(f"mine={sys.argv[1]} n={len(mine)} sum={sum(mine)}")
print(f"theirs={sys.argv[2]} n={len(theirs)} sum={sum(theirs)}")
print(f"compared={n} equal={n - len(differ)} differ={len(differ)}")
if len(mine) != len(theirs):
    print(f"length_mismatch {len(mine)} {len(theirs)}")
for i in differ[:15]:
    print(f"diff {i} mine {mine[i]} theirs {theirs[i]}")
