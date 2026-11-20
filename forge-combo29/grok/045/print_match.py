#!/usr/bin/env python3
"""Print the fastchess results block from a match log."""
import sys

lines = open(sys.argv[1]).read().splitlines()
start = None
for i, line in enumerate(lines):
    if line.startswith("Results of "):
        start = i
print("file", sys.argv[1])
if start is None:
    print("NO RESULTS BLOCK")
    raise SystemExit(1)
for line in lines[start - 1 : start + 8]:
    print(line)
