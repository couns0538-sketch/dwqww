#!/usr/bin/env python3
"""Print the fastchess results block and the finished-game count."""
import sys
from pathlib import Path

text = Path(sys.argv[1]).read_text(errors="replace")
finished = sum(1 for line in text.splitlines() if line.startswith("Finished game "))
print(f"finished_games {finished}")
start = text.rfind("Results of ")
if start < 0:
    print("NO RESULTS BLOCK")
    raise SystemExit(1)
end = text.find("Finished match", start)
block = text[start:end if end >= 0 else None]
print(block.rstrip())
if end >= 0:
    rest = text[end:].splitlines()
    print(rest[0])
    if len(rest) > 1:
        print(rest[1])
