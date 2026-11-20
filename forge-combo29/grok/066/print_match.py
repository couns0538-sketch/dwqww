#!/usr/bin/env python3
"""Print the fastchess results block from a match log."""
import sys
from pathlib import Path

text = Path(sys.argv[1]).read_text().splitlines()
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
