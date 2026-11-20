#!/usr/bin/env python3
"""Read a fastchess log and print the score and Elo lines it actually contains."""
import sys
from pathlib import Path

text = Path(sys.argv[1]).read_text(errors="replace")
finished = 0
for line in text.splitlines():
    if line.startswith("Finished game "):
        finished += 1
    if (
        line.startswith("Score of ")
        or line.startswith("Results of ")
        or line.startswith("Elo:")
        or line.startswith("Games:")
        or line.startswith("LOS:")
        or "Elo difference" in line
    ):
        print(line)
print(f"finished_games {finished}")
if "MATCH_EXIT:" in text:
    for line in text.splitlines():
        if line.startswith("MATCH_EXIT:"):
            print(line)
