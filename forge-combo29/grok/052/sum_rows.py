#!/usr/bin/env python3
"""Print node sum and the first three rows of a search_set .rows file."""
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
rows = [line.split("\t") for line in path.read_text().splitlines() if line]
total = sum(int(row[1]) for row in rows)
print(f"file {path.name}")
print(f"positions {len(rows)}")
print(f"sum {total}")
for row in rows[:3]:
    print(f"first {row[0]} {row[1]}")
