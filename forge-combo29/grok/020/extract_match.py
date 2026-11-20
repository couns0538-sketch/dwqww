#!/usr/bin/env python3
"""Print the last fastchess results block from a log."""
import sys
from pathlib import Path

lines = Path(sys.argv[1]).read_text().splitlines()
starts = [i for i, line in enumerate(lines) if line.startswith("Results of ")]
if not starts:
    raise SystemExit("no results")
start = starts[-1]
for line in lines[start:]:
    print(line)
    if line.startswith("Total Time:"):
        break
