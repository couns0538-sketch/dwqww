#!/usr/bin/env python3
"""Print the last fastchess results block from match_on_vs_off.log."""
from pathlib import Path

lines = Path(__file__).with_name("match_on_vs_off.log").read_text(errors="replace").splitlines()
blocks = []
cur = []
for line in lines:
    if line.startswith("Results of "):
        if cur:
            blocks.append(cur)
        cur = [line]
    elif cur:
        cur.append(line)
        if line.startswith("Ptnml"):
            blocks.append(cur)
            cur = []
if cur:
    blocks.append(cur)
if not blocks:
    raise SystemExit("no results block")
print("\n".join(blocks[-1]))
