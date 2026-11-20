#!/usr/bin/env python3
"""Compare node columns of two run_set tsv files. Prints a one-row summary."""
import sys
from pathlib import Path

def nodes(path):
    rows = []
    for line in Path(path).read_text().splitlines()[1:]:
        if not line or line.startswith("SUM"):
            continue
        parts = line.split("\t")
        rows.append(int(parts[1]))
    return rows

a = nodes(sys.argv[1])
b = nodes(sys.argv[2])
if len(a) != len(b):
    print(f"length {len(a)} {len(b)}")
    sys.exit(1)
differ = sum(x != y for x, y in zip(a, b))
print(f"positions={len(a)} differ={differ} sum_a={sum(a)} sum_b={sum(b)}")
