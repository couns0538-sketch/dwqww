#!/usr/bin/env python3
"""Print the last fastchess results block from a match log."""

import sys
from pathlib import Path

text = Path(sys.argv[1]).read_text(encoding="utf-8", errors="replace").splitlines()
starts = [i for i, line in enumerate(text) if line.startswith("Results of ")]
if not starts:
    raise SystemExit("no results block")
start = starts[-1]
for line in text[start:]:
    print(line)
    if line.startswith("Total Time:"):
        break
