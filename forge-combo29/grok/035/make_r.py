#!/usr/bin/env python3
"""Random legal games with SEED. Keep a position every 7 plies starting at ply 15.
A game that ends before ply 15 is dropped. Terminal positions are not kept.
"""
import random
import sys
import chess

SEED = 35 * 100 + 1
WANT = int(sys.argv[1]) if len(sys.argv) > 1 else 300
OUT = sys.argv[2]
rng = random.Random(SEED)
kept = []
games = 0
dropped = 0
while len(kept) < WANT:
    games += 1
    board = chess.Board()
    samples = []
    ended_early = False
    while board.ply() < 80:
        if board.is_game_over(claim_draw=True):
            ended_early = board.ply() < 15
            break
        ply = board.ply()
        if ply >= 15 and (ply - 15) % 7 == 0:
            samples.append(board.fen())
        board.push(rng.choice(list(board.legal_moves)))
    else:
        if board.is_game_over(claim_draw=True) and board.ply() < 15:
            ended_early = True
    if ended_early or not samples:
        dropped += 1
        continue
    for fen in samples:
        if len(kept) >= WANT:
            break
        kept.append(fen)
text = "\n".join(kept) + "\n"
open(OUT, "w").write(text)
print(f"seed {SEED} games {games} dropped {dropped} positions {len(kept)}")
