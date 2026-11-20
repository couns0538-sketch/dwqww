#!/usr/bin/env python3
"""Random legal games. One position every 7 plies after ply 8. Games that end are dropped."""
import random
import sys
from pathlib import Path

import chess

SEED = int(sys.argv[1])
COUNT = int(sys.argv[2])
OUT = Path(sys.argv[3])
# A game that reaches this ply without ending is kept. One that ends before it is dropped.
MAX_PLY = 80
# Plies 15, 22, 29, ... : every 7 plies after ply 8.
SAMPLE_FROM = 8
SAMPLE_EVERY = 7

rng = random.Random(SEED)
kept = []
started = 0
dropped = 0
while len(kept) < COUNT:
    started += 1
    board = chess.Board()
    samples = []
    ended = False
    for ply in range(1, MAX_PLY + 1):
        moves = list(board.legal_moves)
        if not moves or board.is_game_over(claim_draw=True):
            ended = True
            break
        board.push(rng.choice(moves))
        if ply > SAMPLE_FROM and (ply - SAMPLE_FROM) % SAMPLE_EVERY == 0:
            if board.is_game_over(claim_draw=True):
                ended = True
                break
            samples.append(board.fen())
    if ended or len(samples) == 0:
        dropped += 1
        continue
    kept.extend(samples)
OUT.write_text("\n".join(kept[:COUNT]) + "\n")
print(f"seed {SEED} started {started} dropped {dropped} wrote {COUNT} to {OUT}")
