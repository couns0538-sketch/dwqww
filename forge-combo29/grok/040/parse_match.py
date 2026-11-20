#!/usr/bin/env python3
"""Print the fastchess results block from a match log."""
import sys
from pathlib import Path
lines = Path(sys.argv[1]).read_text(errors="replace").splitlines()
start = None
for i, line in enumerate(lines):
    if line.startswith("Results of "):
        start = i - 1 if i and set(lines[i - 1]) == {"-"} else i
end = None
if start is not None:
    for j in range(start + 1, len(lines)):
        if lines[j].startswith("Finished match"):
            end = j
            break
if start is None or end is None:
    raise SystemExit("no results block")
print("\n".join(lines[start:end + 1]))
