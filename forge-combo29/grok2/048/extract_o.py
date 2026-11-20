#!/usr/bin/env python3
"""extract_o.py RAW [RAW ...]
Reads o_run transcripts. For each go depth 12, prints position number and
the nodes field of the last info line before bestmove.
Then a summary line: sum, first three, and (if a second file is given)
how many positions differ from the first file.
"""
import re
import sys
from pathlib import Path

def nodes_of(path):
    lines = Path(path).read_text(encoding="utf-8", errors="replace").splitlines()
    rows = []
    i = 0
    while i < len(lines):
        if lines[i] == ">> go depth 12":
            last_info = None
            i += 1
            while i < len(lines) and not lines[i].startswith(">> "):
                if lines[i].startswith("info "):
                    last_info = lines[i]
                if lines[i].startswith("bestmove "):
                    break
                i += 1
            if last_info is None:
                sys.exit(f"STOP no info line before bestmove in {path} position {len(rows)+1}")
            m = re.search(r" nodes (\d+)", last_info)
            if not m:
                sys.exit(f"STOP last info has no nodes in {path} position {len(rows)+1}: {last_info}")
            rows.append(int(m.group(1)))
        else:
            i += 1
    return rows

files = sys.argv[1:]
if not files:
    sys.exit("usage: extract_o.py RAW [RAW ...]")
parsed = []
for f in files:
    rows = nodes_of(f)
    parsed.append(rows)
    print(f"file {f}")
    print(f"count {len(rows)}")
    print(f"sum {sum(rows)}")
    if len(rows) >= 3:
        print(f"first {rows[0]} {rows[1]} {rows[2]}")
    if parsed:
        base = parsed[0]
        if rows is not base and len(rows) == len(base):
            differ = sum(1 for a, b in zip(base, rows) if a != b)
            print(f"differ_from_first {differ}")
    print("---")
