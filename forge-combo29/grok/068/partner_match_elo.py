#!/usr/bin/env python3
"""Print the fastchess results block from partner_match_stdout.txt."""
from pathlib import Path

text = Path(__file__).resolve().parent.joinpath("partner_match_stdout.txt").read_text().splitlines()
start = None
for index, line in enumerate(text):
    if line.startswith("Results of "):
        start = index
if start is None:
    raise SystemExit("no results block")
for line in text[start - 1 :]:
    print(line)
    if line.startswith("Total Time:"):
        break
