#!/usr/bin/env python3
"""Print the Elo block from a fastchess result file. No numbers are typed here."""
import sys
from pathlib import Path

text = Path(sys.argv[1]).read_text(errors="replace")
start = text.rfind("Results of ")
if start < 0:
    raise SystemExit("no results block")
block = text[start:]
end = block.find("Finished match")
if end >= 0:
    block = block[:end]
print(block.rstrip())
print("---")
for line in block.splitlines():
    if line.startswith("Elo:") or line.startswith("Games:"):
        print(line)
