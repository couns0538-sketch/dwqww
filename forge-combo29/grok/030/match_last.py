#!/usr/bin/env python3
"""Print the last fastchess Results block and the Finished match lines."""
import sys
from pathlib import Path

text = Path(sys.argv[1]).read_text().splitlines()
starts = [i for i, line in enumerate(text) if line.startswith("Results of ")]
if not starts:
    raise SystemExit("no results")
start = starts[-1]
for line in text[start:]:
    print(line)
    if line.startswith("Total Time:"):
        break
print(f"finished_games={sum(1 for line in text if line.startswith('Finished game '))}")
