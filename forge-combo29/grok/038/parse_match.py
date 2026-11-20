#!/usr/bin/env python3
"""Print the last Results block from a fastchess log."""
import sys
from pathlib import Path

lines = Path(sys.argv[1]).read_text(errors="replace").splitlines()
starts = [i for i, line in enumerate(lines) if line.startswith("Results of ")]
if not starts:
    raise SystemExit("no results")
start = starts[-1]
for line in lines[start:]:
    if line.startswith("match_exit"):
        break
    print(line)
    if line.startswith("Finished match"):
        break
