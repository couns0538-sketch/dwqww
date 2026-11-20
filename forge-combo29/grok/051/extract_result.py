#!/usr/bin/env python3
"""Print the final fastchess results block from a raw log."""
import sys
from pathlib import Path

lines = Path(sys.argv[1]).read_text().splitlines()
start = None
for i, line in enumerate(lines):
    if line.startswith("Results of "):
        start = i - 1 if i > 0 and set(lines[i - 1]) == {"-"} else i
if start is None:
    print("no results block")
    sys.exit(1)
for line in lines[start:]:
    print(line)
    if line.strip() == "Finished match":
        break
