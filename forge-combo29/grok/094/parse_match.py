#!/usr/bin/env python3
"""Print the last Elo line and the last Games line from a fastchess log."""

import sys
from pathlib import Path

path = Path(sys.argv[1])
elo = None
games = None
for line in path.read_text().splitlines():
    if line.startswith("Elo:"):
        elo = line
    if line.startswith("Games:"):
        games = line
print(elo if elo else "NO ELO")
print(games if games else "NO GAMES")
