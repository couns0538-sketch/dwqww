#!/usr/bin/env python3
"""o_table.py RAW [RAW ...]  reads engine transcripts. One row per bestmove: index and nodes of the last info line."""
import re
import sys

def rows(path):
    out = []
    last_info = None
    for line in open(path, encoding="utf-8"):
        line = line.rstrip("\n")
        if line.startswith("info "):
            last_info = line
        elif line.startswith("bestmove "):
            m = re.search(r" nodes (\d+)", last_info or "")
            if m is None:
                sys.exit(f"STOP no nodes on last info before bestmove {len(out)+1} in {path}: {last_info}")
            out.append(int(m.group(1)))
            last_info = None
    return out

def show(path):
    r = rows(path)
    print(f"{path} n={len(r)} sum={sum(r)} first3={r[0]} {r[1]} {r[2]}")
    return r

base = show(sys.argv[1])
for path in sys.argv[2:]:
    r = show(path)
    differ = sum(1 for a, b in zip(base, r) if a != b)
    if len(r) != len(base):
        print(f"length {len(r)} != {len(base)}")
    else:
        print(f"differ_from_{sys.argv[1]} {differ}")
