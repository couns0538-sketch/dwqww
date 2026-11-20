#!/usr/bin/env python3
"""Random legal games. Drop a game that ends before ply 43. Keep plies 15,22,29,36,43.

SEED = seat * 100 + 1. Game attempt i uses random.Random(SEED + i).
"""
import random
import sys
import chess

SEED = 101
SAMPLES = (15, 22, 29, 36, 43)
NEED = 300
out = sys.argv[1]

kept = []
dropped = 0
attempt = 0
while len(kept) < NEED:
    rng = random.Random(SEED + attempt)
    board = chess.Board()
    fens = []
    ended = False
    for ply in range(1, SAMPLES[-1] + 1):
        moves = list(board.legal_moves)
        if not moves or board.is_game_over(claim_draw=True):
            ended = True
            break
        board.push(rng.choice(moves))
        if ply in SAMPLES:
            fens.append(board.fen())
        if board.is_game_over(claim_draw=True):
            ended = True
            break
    attempt += 1
    if ended or len(fens) != len(SAMPLES):
        dropped += 1
        continue
    kept.extend(fens)

kept = kept[:NEED]
open(out, "w").write("\n".join(kept) + "\n")
print(f"positions={len(kept)} attempts={attempt} dropped_games={dropped} seed0={SEED} file={out}")
