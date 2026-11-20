#!/usr/bin/env python3
"""Random legal positions. SEED = seat * 100 + 1. See decisions.txt."""
import random
import sys
import chess

SEED = 10401
TARGET = int(sys.argv[1]) if len(sys.argv) > 1 else 400
OUT = sys.argv[2] if len(sys.argv) > 2 else "R.fens"
rng = random.Random(SEED)
kept = []
games = 0
dropped = 0
while len(kept) < TARGET and games < 5000:
    games += 1
    board = chess.Board()
    samples = []
    ended = False
    for ply in range(1, 81):
        moves = list(board.legal_moves)
        if not moves or board.is_game_over(claim_draw=True):
            ended = True
            break
        board.push(rng.choice(moves))
        if ply >= 15 and (ply - 15) % 7 == 0:
            samples.append(board.fen())
    if ended or board.is_game_over(claim_draw=True):
        dropped += 1
        continue
    kept.extend(samples)
kept = kept[:TARGET]
open(OUT, "w").write("\n".join(kept) + "\n")
print(f"games={games} dropped={dropped} positions={len(kept)} seed={SEED}")
