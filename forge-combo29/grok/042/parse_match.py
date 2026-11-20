#!/usr/bin/env python3
"""Read a fastchess log and print the result lines. No hand-typed numbers."""
import re
import sys
from pathlib import Path

text = Path(sys.argv[1]).read_text(errors="replace")
finished = re.findall(r"^Finished game (\d+) .*", text, re.M)
started = re.findall(r"^Started game (\d+) of (\d+)", text, re.M)
print(f"started {len(started)} finished {len(finished)}")
if started:
    print(f"last_started {started[-1][0]} of {started[-1][1]}")
for line in text.splitlines():
    if "Elo:" in line or line.startswith("Score of") or line.startswith("Finished match") or line.startswith("exit "):
        print(line)
results = re.findall(r"^Finished game \d+ \([^)]+\): ([0-9/]+-[0-9/]+)", text, re.M)
wins = draws = losses = 0
for result in results:
    if result == "1-0":
        wins += 1
    elif result == "0-1":
        losses += 1
    elif result == "1/2-1/2":
        draws += 1
print(f"from_log_white_perspective_of_each_game wins {wins} losses {losses} draws {draws} games {wins + losses + draws}")
