#!/usr/bin/env python3
"""Print the last fastchess results block from a match transcript."""
import sys
from pathlib import Path

text = Path(sys.argv[1]).read_text(errors="replace").splitlines()
starts = [i for i, line in enumerate(text) if line.startswith("Results of ")]
if not starts:
    raise SystemExit("no results block")
begin = starts[-1]
end = begin + 1
while end < len(text) and text[end] != "--------------------------------------------------":
    end += 1
block = text[begin:end]
print("\n".join(block))
games = sum(1 for line in text if line.startswith("Finished game "))
print(f"finished_games {games}")
