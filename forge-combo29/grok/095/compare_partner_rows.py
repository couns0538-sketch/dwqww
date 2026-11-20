#!/usr/bin/env python3
"""Compare my harness tsv to the partner's published rows (index nodes move)."""
import pathlib
import sys

def tsv_rows(path: pathlib.Path):
    out = []
    for line in path.read_text().splitlines()[1:]:
        if not line.strip():
            continue
        index, nodes, best, _fen = line.split("\t", 3)
        out.append((int(index), int(nodes), best))
    return out

def partner_rows(path: pathlib.Path):
    out = []
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        index, nodes, best = line.split()
        out.append((int(index), int(nodes), best))
    return out

mine = tsv_rows(pathlib.Path(sys.argv[1]))
theirs = partner_rows(pathlib.Path(sys.argv[2]))
n = min(len(mine), len(theirs))
differ = 0
first = []
for i in range(n):
    if mine[i] != theirs[i]:
        differ += 1
        if len(first) < 8:
            first.append(f"{i} mine {mine[i][1]} {mine[i][2]} theirs {theirs[i][1]} {theirs[i][2]}")
print(f"MINE {sys.argv[1]} N {len(mine)} SUM {sum(r[1] for r in mine)}")
print(f"THEIRS {sys.argv[2]} N {len(theirs)} SUM {sum(r[1] for r in theirs)}")
print(f"COMPARED {n}")
print(f"DIFFER {differ}")
print(f"SAME {n - differ}")
for row in first:
    print(row)
