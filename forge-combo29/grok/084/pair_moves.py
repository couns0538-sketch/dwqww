#!/usr/bin/env python3
"""Compare the two games of each opening. Usage: pair_moves.py PGN"""
import sys
from pathlib import Path

import chess.pgn

path = Path(sys.argv[1])
by_fen: dict[str, dict[str, list[str]]] = {}
games = 0
with path.open(encoding="utf-8", errors="replace") as handle:
    while True:
        game = chess.pgn.read_game(handle)
        if game is None:
            break
        games += 1
        fen = game.headers.get("FEN", chess.STARTING_FEN)
        white = game.headers.get("White", "")
        moves = [move.uci() for move in game.mainline_moves()]
        by_fen.setdefault(fen, {})[white] = moves
same = 0
differ = 0
missing = 0
for fen, sides in by_fen.items():
    if "on" not in sides or "off" not in sides:
        missing += 1
        continue
    if sides["on"] == sides["off"]:
        same += 1
    else:
        differ += 1
        if differ <= 3:
            print(f"differ fen {fen}")
            print("on ", " ".join(sides["on"][:16]))
            print("off", " ".join(sides["off"][:16]))
print(f"openings {len(by_fen)}")
print(f"same_moves {same}")
print(f"differ_moves {differ}")
print(f"missing_side {missing}")
print(f"games {games}")
