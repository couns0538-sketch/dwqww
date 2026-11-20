#!/usr/bin/env python3
"""Pull one node count per bestmove from a raw UCI log, in order."""
import pathlib
import sys

last = None
rows = []
for line in pathlib.Path(sys.argv[1]).read_text(errors="replace").splitlines():
    if line.startswith("info depth "):
        parts = line.split()
        for i, part in enumerate(parts):
            if part == "nodes" and i + 1 < len(parts):
                last = int(parts[i + 1])
    elif line.startswith("bestmove ") and last is not None:
        rows.append(last)
        last = None
out = pathlib.Path(sys.argv[2])
out.write_text("".join(f"{i} {nodes}\n" for i, nodes in enumerate(rows, start=1)))
print(f"n={len(rows)} sum={sum(rows)} first={' '.join(str(n) for n in rows[:3])}")
