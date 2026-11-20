#!/usr/bin/env python3
"""Print the fastchess summary block from a match transcript."""
import sys
from pathlib import Path

text = Path(sys.argv[1]).read_text(errors="replace").splitlines()
start = None
for i, line in enumerate(text):
    if line.startswith("Results of "):
        start = i
if start is None:
    print("no results block")
    raise SystemExit(1)
for line in text[start:]:
    print(line)
    if line.startswith("Finished match"):
        break
