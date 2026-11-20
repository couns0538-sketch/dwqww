#!/usr/bin/env python3
"""Print the fastchess results block and the game count from a match log."""
import sys

path = sys.argv[1]
text = open(path, encoding="utf-8", errors="replace").read().splitlines()
finished = 0
for line in text:
    if line.startswith("Finished game "):
        finished += 1
print(f"finished_games {finished}")
start = None
for index, line in enumerate(text):
    if line.startswith("Results of "):
        start = index
if start is None:
    print("results none")
else:
    for line in text[start:]:
        print(line)
        if line.startswith("----"):
            break
for line in text:
    if line.startswith("fastchess_exit=") or line.startswith("start ") or line.startswith("end ") or line.startswith("Total Time:"):
        print(line)
