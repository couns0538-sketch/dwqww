#!/usr/bin/env python3
"""Print the fastchess summary lines from a match log. No hand-typed numbers."""
import sys
from pathlib import Path

text = Path(sys.argv[1]).read_text(errors="replace")
lines = text.splitlines()
start = 0
for i, line in enumerate(lines):
    if line.startswith("Results of "):
        start = i
for line in lines[start:]:
    print(line)
