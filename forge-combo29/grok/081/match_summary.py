#!/usr/bin/env python3
"""Read a fastchess stdout file and print the result block."""
import sys

path = sys.argv[1]
lines = open(path, encoding="utf-8").read().splitlines()
start = None
for i, line in enumerate(lines):
    if line.startswith("Results of "):
        start = i
if start is None:
    print("no results block")
    sys.exit(1)
for line in lines[start:]:
    print(line)
    if line.startswith("Finished match") or line.startswith("fastchess_exit"):
        break
