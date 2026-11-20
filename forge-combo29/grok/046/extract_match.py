#!/usr/bin/env python3
"""Print the last fastchess result block from a match log."""
import sys
from pathlib import Path

lines = Path(sys.argv[1]).read_text(errors="replace").splitlines()
start = None
for i, line in enumerate(lines):
    if line.startswith("Results of "):
        start = i
if start is None:
    print("no result block")
    raise SystemExit(1)
for line in lines[start:]:
    print(line)
    if line.startswith("fastchess_exit") or line.startswith("Finished match"):
        if line.startswith("Finished match"):
            # include the following total-time and exit lines if present
            continue
print("--- tail ---")
for line in lines[-8:]:
    print(line)
