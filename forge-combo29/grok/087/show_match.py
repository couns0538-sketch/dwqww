#!/usr/bin/env python3
"""Print the fastchess Results block from a match log."""
import sys

text = open(sys.argv[1], "r", encoding="utf-8", errors="replace").read().splitlines()
start = None
for i, line in enumerate(text):
    if line.startswith("Results of "):
        start = i
if start is None:
    sys.stderr.write("no results block\n")
    sys.exit(2)
for line in text[start:]:
    print(line)
    if line.startswith("Finished match") or line.startswith("Total Time:"):
        if line.startswith("Total Time:"):
            break
