#!/usr/bin/env python3
"""Print the last Elo block from a fastchess log."""
import sys
from pathlib import Path

text = Path(sys.argv[1]).read_text(encoding="utf-8", errors="replace")
lines = text.splitlines()
finished = sum(1 for line in lines if line.startswith("Finished game"))
print(f"finished_games {finished}")
start = None
for i, line in enumerate(lines):
    if line.startswith("Results of "):
        start = i
if start is None:
    print("no results block")
    sys.exit(0)
for line in lines[start:]:
    if line.startswith("Finished match") or line.startswith("Total Time") or line.startswith("match_exit"):
        print(line)
        continue
    if line.startswith("---") or line.startswith("Results of ") or line.startswith("Elo:") or line.startswith("Games:"):
        print(line)
