#!/usr/bin/env python3
"""Random legal games. SEED = seat * 100 + 1. Drop a game that ends."""
import random
import chess

SEED = 105 * 100 + 1
TARGET = 300
MAX_PLY = 64
rng = random.Random(SEED)
kept = []
games = 0
dropped = 0
while len(kept) < TARGET:
    board = chess.Board()
    samples = []
    ended = False
    for ply in range(1, MAX_PLY + 1):
        if board.is_game_over(claim_draw=True):
            ended = True
            break
        move = rng.choice(list(board.legal_moves))
        board.push(move)
        if ply >= 8 and (ply - 8) % 7 == 0:
            samples.append(board.fen())
    games += 1
    if ended or board.is_game_over(claim_draw=True):
        dropped += 1
        continue
    kept.extend(samples)
path = __file__.replace("make_r.py", "R.fens")
with open(path, "w", encoding="utf-8") as handle:
    for fen in kept[:TARGET]:
        handle.write(fen + "\n")
print(f"seed={SEED} games={games} dropped={dropped} wrote={min(TARGET, len(kept))} {path}")
