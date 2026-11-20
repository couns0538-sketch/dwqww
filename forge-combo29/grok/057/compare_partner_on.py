#!/usr/bin/env python3
"""Compare my suite rows to a partner TSV of index, nodes, move.
Usage: compare_partner_on.py <my.rows.txt> <partner.tsv>
"""
import sys

def my_nodes(path):
    out = []
    for line in open(path):
        line = line.strip()
        if line:
            out.append(int(line.split()[1]))
    return out

def their_nodes(path):
    out = []
    for line in open(path):
        line = line.strip()
        if not line:
            continue
        parts = line.split()
        out.append(int(parts[1]))
    return out

a = my_nodes(sys.argv[1])
b = their_nodes(sys.argv[2])
if len(a) != len(b):
    raise SystemExit(f"length {len(a)} vs {len(b)}")
differ = sum(1 for x, y in zip(a, b) if x != y)
print(f"n {len(a)}")
print(f"sum_mine {sum(a)}")
print(f"sum_theirs {sum(b)}")
print(f"differ {differ}")
print(f"equal {len(a) - differ}")
