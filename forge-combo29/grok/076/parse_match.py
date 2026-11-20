#!/usr/bin/env python3
"""Print the last fastchess Results block from a match log."""
import sys

text = open(sys.argv[1]).read().splitlines()
start = None
for i, line in enumerate(text):
    if line.startswith("Results of "):
        start = i
if start is None:
    raise SystemExit("no results block")
for line in text[start:]:
    print(line)
    if line.startswith("Total Time:"):
        break
finished = sum(1 for line in text if line.startswith("Finished game "))
print("finished_lines", finished)
