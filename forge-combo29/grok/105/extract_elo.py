#!/usr/bin/env python3
"""Print the last fastchess results block from a match log."""
import pathlib
import sys

text = pathlib.Path(sys.argv[1]).read_text(errors="replace").splitlines()
start = None
for i, line in enumerate(text):
    if line.startswith("Results of "):
        start = i
if start is None:
    raise SystemExit("no results block")
for line in text[start:]:
    print(line)
    if line.startswith("Finished match"):
        break
