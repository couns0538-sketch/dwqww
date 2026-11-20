#!/usr/bin/env python3
"""Last info-depth node count before each bestmove. Reads a UCI transcript."""
import sys
from pathlib import Path

lines = Path(sys.argv[1]).read_text(errors="replace").splitlines()
pending = []
rows = []
for line in lines:
    if line.startswith("info ") and " depth " in line and " nodes " in line:
        parts = line.split()
        depth = parts[parts.index("depth") + 1]
        nodes = parts[parts.index("nodes") + 1]
        pending.append((depth, nodes))
    elif line.startswith("bestmove ") or line.startswith("> bestmove"):
        if not pending:
            raise SystemExit("bestmove with no info")
        depth, nodes = pending[-1]
        rows.append((len(rows) + 1, nodes, depth))
        pending = []
out = Path(sys.argv[2])
with out.open("w") as handle:
    handle.write("index\tnodes\tdepth\n")
    for index, nodes, depth in rows:
        handle.write(f"{index}\t{nodes}\t{depth}\n")
print(f"rows {len(rows)} sum {sum(int(nodes) for _, nodes, _ in rows)}")
