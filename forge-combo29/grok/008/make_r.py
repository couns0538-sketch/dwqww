#!/usr/bin/env python3
"""300 positions from random legal games. SEED = seat*100+1 = 801.

A game is played to ply 80. If it ends before that, the game is dropped.
From a game that reaches ply 80, one position is kept every 7 plies
starting at ply 8 (plies 8, 15, 22, ...).
"""
import random
import sys
from pathlib import Path

import chess

SEED = 801
TARGET = 300
CAP = 80
rng = random.Random(SEED)
kept = []
seen = 0
dropped = 0
while len(kept) < TARGET:
    seen += 1
    if seen > 20000:
        raise SystemExit("too many games")
    board = chess.Board()
    fens = []
    ended = False
    for _ply in range(1, CAP + 1):
        if board.is_game_over(claim_draw=True):
            ended = True
            break
        move = rng.choice(list(board.legal_moves))
        board.push(move)
        if board.is_game_over(claim_draw=True):
            ended = True
            break
        fens.append(board.fen())
    if ended or len(fens) < CAP:
        dropped += 1
        continue
    for ply in range(8, CAP + 1, 7):
        kept.append(fens[ply - 1])
        if len(kept) >= TARGET:
            break
out = Path(sys.argv[1])
out.write_text("".join(fen + "\n" for fen in kept[:TARGET]))
print(f"positions {TARGET}")
print(f"games_seen {seen}")
print(f"games_dropped {dropped}")
print(f"seed {SEED}")
print(f"file {out}")
