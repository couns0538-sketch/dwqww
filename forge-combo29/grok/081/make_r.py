#!/usr/bin/env python3
"""300 positions from random legal games.

SEED = seat * 100 + 1. A game that ends before ply 64 is dropped.
From a game that is still going at ply 64, one FEN is kept every 7 plies
starting at ply 8 (8, 15, 22, ...). The terminal position is never kept.
"""
import random
import sys

import chess

SEED = 81 * 100 + 1
NEED = 300
LAST_PLY = 64
rng = random.Random(SEED)
kept = []
started = 0
dropped = 0
while len(kept) < NEED:
    board = chess.Board()
    samples = []
    ended = False
    started += 1
    for ply in range(1, LAST_PLY + 1):
        if board.is_game_over(claim_draw=True):
            ended = True
            break
        board.push(rng.choice(list(board.legal_moves)))
        if ply >= 8 and (ply - 8) % 7 == 0:
            if board.is_game_over(claim_draw=True):
                ended = True
                break
            samples.append(board.fen())
    if ended or board.is_game_over(claim_draw=True):
        dropped += 1
        continue
    for fen in samples:
        if len(kept) >= NEED:
            break
        kept.append(fen)
out = sys.argv[1]
with open(out, "w", encoding="utf-8") as handle:
    for fen in kept:
        handle.write(fen + "\n")
print("seed %d positions %d games_started %d games_dropped %d" % (SEED, len(kept), started, dropped))
