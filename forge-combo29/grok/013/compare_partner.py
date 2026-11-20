#!/usr/bin/env python3
"""Compare my rows tsv with either another rows tsv or the partner's 'index nodes' file."""
import sys
from pathlib import Path

def load_tsv(path):
    rows = []
    for line in Path(path).read_text().splitlines():
        if not line.strip():
            continue
        parts = line.split("\t")
        rows.append((int(parts[0]), int(parts[1])))
    return rows

def load_partner(path):
    rows = []
    for line in Path(path).read_text().splitlines():
        if not line.strip():
            continue
        index, nodes = line.split()
        rows.append((int(index) + 1, int(nodes)))
    return rows

mine = load_tsv(sys.argv[1])
other = load_partner(sys.argv[2]) if sys.argv[3] == "partner" else load_tsv(sys.argv[2])
if len(mine) != len(other):
    print(f"length {len(mine)} {len(other)}")
    sys.exit(1)
differ = sum(1 for a, b in zip(mine, other) if a[1] != b[1] or a[0] != b[0])
print(f"count {len(mine)} differ {differ} equal {len(mine) - differ}")
