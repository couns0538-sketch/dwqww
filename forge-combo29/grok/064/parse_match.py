#!/usr/bin/env python3
"""Print the last fastchess Results block. Paste this output."""
import pathlib
import sys

lines = pathlib.Path(sys.argv[1]).read_text().splitlines()
starts = [i for i, line in enumerate(lines) if line.startswith("Results of ")]
if not starts:
    raise SystemExit("no results block")
start = starts[-1]
end = start + 1
while end < len(lines) and lines[end] != "--------------------------------------------------":
    end += 1
print("\n".join(lines[start:end]))
