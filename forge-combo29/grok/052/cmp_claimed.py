#!/usr/bin/env python3
"""Compare my .rows nodes to a partner nodes file of 'index depth nodes'."""
import pathlib
import sys

rows = [line.split("\t") for line in pathlib.Path(sys.argv[1]).read_text().splitlines() if line]
claimed = []
for line in pathlib.Path(sys.argv[2]).read_text().splitlines():
    if not line.strip():
        continue
    parts = line.split()
    claimed.append(parts)
print(f"rows {len(rows)} claimed {len(claimed)}")
n = min(len(rows), len(claimed))
differ = 0
first = []
for i in range(n):
    if rows[i][1] != claimed[i][2]:
        differ += 1
        if len(first) < 5:
            first.append(f"{rows[i][0]} mine {rows[i][1]} claimed {claimed[i][2]}")
print(f"compared {n}")
print(f"differ {differ}")
print(f"same {n - differ}")
for line in first:
    print(line)
