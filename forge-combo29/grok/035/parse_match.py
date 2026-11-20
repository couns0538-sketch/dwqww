#!/usr/bin/env python3
"""Print the last fastchess results block and the finished-game count."""
import sys
from pathlib import Path

text = Path(sys.argv[1]).read_text(errors="replace").splitlines()
finished = sum(1 for line in text if line.startswith("Finished game "))
print(f"finished_games {finished}")
blocks = []
cur = []
for line in text:
    if line.startswith("Results of "):
        cur = [line]
    elif cur:
        cur.append(line)
        if line.startswith("---") and len(cur) > 2:
            blocks.append(cur)
            cur = []
if not blocks:
    raise SystemExit("no results block")
print("\n".join(blocks[-1]))
