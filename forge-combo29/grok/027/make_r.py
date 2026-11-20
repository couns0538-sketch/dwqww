#!/usr/bin/env python3
"""Random legal games with SEED. Keep a game only if it is still going at ply 80.

Sample one position every 7 plies from ply 8 (8, 15, 22, ...). A game that ends
before ply 80 is dropped, including its earlier positions. python-chess claims
the 50-move rule and threefold repetition as the end of the game.
"""
import random
from pathlib import Path

import chess

SEED = 2701
WANT = 300
MAX_PLY = 80
OUT = Path(__file__).resolve().parent / "R.fens"

rng = random.Random(SEED)
kept_games = 0
dropped = 0
positions: list[str] = []
while len(positions) < WANT:
    board = chess.Board()
    sample: list[str] = []
    ended = False
    for ply in range(1, MAX_PLY + 1):
        if board.is_game_over(claim_draw=True):
            ended = True
            break
        moves = list(board.legal_moves)
        if not moves:
            ended = True
            break
        board.push(rng.choice(moves))
        if ply >= 8 and (ply - 8) % 7 == 0 and not board.is_game_over(claim_draw=True):
            sample.append(board.fen())
    if ended or board.is_game_over(claim_draw=True):
        dropped += 1
        continue
    kept_games += 1
    for fen in sample:
        if len(positions) >= WANT:
            break
        positions.append(fen)

OUT.write_text("".join(fen + "\n" for fen in positions), encoding="utf-8")
note = (
    f"seed={SEED}\n"
    f"want={WANT}\n"
    f"max_ply={MAX_PLY}\n"
    f"kept_games={kept_games}\n"
    f"dropped_games={dropped}\n"
    f"positions={len(positions)}\n"
    "rule=drop a game that ends at or before ply 80; sample plies 8,15,22,... while the game is still going\n"
)
(OUT.with_suffix(".meta")).write_text(note, encoding="utf-8")
print(note, end="")
