#!/usr/bin/env python3
"""Compare my harness tsv nodes to a partner row file (index nodes depth fen) or another tsv."""
import sys

def load_tsv(path):
    rows = {}
    for line in open(path, encoding="utf-8"):
        parts = line.rstrip("\n").split("\t")
        if not parts or parts[0] in ("index", "SUM") or not parts[0].isdigit():
            continue
        rows[int(parts[0])] = int(parts[1])
    return rows

def load_rows(path):
    rows = {}
    total = None
    for line in open(path, encoding="utf-8"):
        parts = line.split()
        if not parts:
            continue
        if parts[0] == "SUM" and len(parts) >= 2 and parts[1].isdigit():
            total = int(parts[1])
            continue
        if parts[0].isdigit() and len(parts) >= 2 and parts[1].isdigit():
            rows[int(parts[0])] = int(parts[1])
    return rows, total

mine = load_tsv(sys.argv[1])
theirs, claimed = load_rows(sys.argv[2])
keys = sorted(set(mine) | set(theirs))
differ = 0
missing = 0
for key in keys:
    if key not in mine or key not in theirs:
        missing += 1
        continue
    if mine[key] != theirs[key]:
        differ += 1
mysum = sum(mine.values())
print(f"mine {len(mine)} sum {mysum} theirs {len(theirs)} claimed_sum {claimed} missing {missing} differ {differ}")
