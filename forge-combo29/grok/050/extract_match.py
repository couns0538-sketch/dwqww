#!/usr/bin/env python3
"""Print the fastchess results block from a match log."""
import sys
from pathlib import Path

lines = Path(sys.argv[1]).read_text().splitlines()
for index, line in enumerate(lines):
    if line.startswith("Results of "):
        start = index - 1 if index and set(lines[index - 1]) == {"-"} else index
        end = index
        while end < len(lines) and not lines[end].startswith("Total Time:"):
            end += 1
        if end < len(lines):
            end += 1
        print("\n".join(lines[start:end]))
        break
else:
    sys.exit("no results block")
