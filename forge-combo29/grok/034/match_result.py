#!/usr/bin/env python3
"""Print the last fastchess results block from a match log."""
import sys

lines = open(sys.argv[1], encoding="utf-8", errors="replace").read().splitlines()
starts = [i for i, line in enumerate(lines) if line.startswith("Results of ")]
if not starts:
    raise SystemExit("no results block")
start = starts[-1]
for line in lines[start:]:
    print(line)
    if line.startswith("Total Time:"):
        break
