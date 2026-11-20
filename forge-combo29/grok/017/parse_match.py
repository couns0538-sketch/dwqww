#!/usr/bin/env python3
"""Print the fastchess result block and a one-line Elo summary."""
import sys

text = open(sys.argv[1], encoding="utf-8", errors="replace").read().splitlines()
blocks = []
current = []
for line in text:
    if line.startswith("Results of "):
        current = [line]
    elif current:
        current.append(line)
        if line.startswith("Games:"):
            blocks.append(current)
            current = []
if not blocks:
    raise SystemExit("no results block")
last = blocks[-1]
print("\n".join(last))
games = wins = losses = draws = None
elo = err = None
for line in last:
    if line.startswith("Elo:"):
        # Elo: -1.23 +/- 4.56, nElo: ...
        parts = line.split(",")[0].replace("Elo:", "").strip().split()
        elo = parts[0]
        if "+/-" in parts:
            err = parts[parts.index("+/-") + 1]
    if line.startswith("Games:"):
        fields = line.replace(",", " ").split()
        # Games: N Wins: N Losses: N Draws: N
        for key, dest in (("Games:", "games"), ("Wins:", "wins"), ("Losses:", "losses"), ("Draws:", "draws")):
            if key in fields:
                value = fields[fields.index(key) + 1]
                if key == "Games:":
                    games = value
                elif key == "Wins:":
                    wins = value
                elif key == "Losses:":
                    losses = value
                else:
                    draws = value
finished = sum(1 for line in text if line.startswith("Finished game "))
print(f"summary elo {elo} err {err} games {games} wins {wins} losses {losses} draws {draws} finished_lines {finished}")
