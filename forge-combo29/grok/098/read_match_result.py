#!/usr/bin/env python3
"""Print the fastchess results block from a match log."""
import sys

path = sys.argv[1]
lines = open(path).read().splitlines()
start = None
for index, line in enumerate(lines):
    if line.startswith("Results of "):
        start = index
if start is None:
    print("no results block")
    sys.exit(1)
for line in lines[start:]:
    print(line)
    if line.strip() == "Finished match":
        break
