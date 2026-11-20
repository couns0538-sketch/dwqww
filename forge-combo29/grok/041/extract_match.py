#!/usr/bin/env python3
"""Print the last fastchess Results block from a match log."""
import sys

lines = open(sys.argv[1], encoding="utf-8").read().splitlines()
starts = [i for i, line in enumerate(lines) if line.startswith("Results of ")]
if not starts:
    raise SystemExit("no results block")
start = starts[-1]
end = start
while end < len(lines) and lines[end] != "Finished match":
    end += 1
    if end > start and lines[end - 1].startswith("---") and end - 1 > start + 1:
        break
print("\n".join(lines[start:end]))
