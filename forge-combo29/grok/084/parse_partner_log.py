#!/usr/bin/env python3
"""Extract depth-search rows from a partner raw log. Usage: parse_partner_log.py LOG OUT"""
import sys
from pathlib import Path

rows = []
last_nodes = None
for line in Path(sys.argv[1]).read_text(errors="replace").splitlines():
    body = line[4:] if line.startswith("<<< ") else line
    if " nodes " in body and body.startswith("info "):
        parts = body.split()
        if "nodes" in parts:
            last_nodes = parts[parts.index("nodes") + 1]
    if body.startswith("bestmove "):
        move = body.split()[1]
        rows.append((last_nodes, move))
        last_nodes = None
out = [f"{index} {nodes} {move}" for index, (nodes, move) in enumerate(rows, start=1)]
Path(sys.argv[2]).write_text("\n".join(out) + "\n")
print(f"rows {len(rows)}")
if rows:
    print(f"first {rows[0][0]} {rows[0][1]}")
    print(f"sum {sum(int(nodes) for nodes, _move in rows)}")
