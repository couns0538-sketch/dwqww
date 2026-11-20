#!/usr/bin/env python3
"""Print node sums from harness .rows files. Reads the files; does not recompute."""
import pathlib
import sys

folder = pathlib.Path(__file__).resolve().parent
names = sys.argv[1:] or ["B_O_d12.rows", "B_G_d12.rows"]
for name in names:
    rows = (folder / name).read_text().splitlines()
    nodes = [int(row.split()[1]) for row in rows if row.strip()]
    first = " ".join(str(n) for n in nodes[:3])
    print(f"{name} positions {len(nodes)} sum {sum(nodes)} first3 {first}")
