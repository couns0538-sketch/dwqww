#!/usr/bin/env python3
"""Random legal games from python-chess. SEED = seat * 100 + 1.

Take one position every 7 plies starting at ply 8 (8, 15, 22, 29, 36).
A game that ends before ply 36 is dropped, including its earlier positions.
"""
import random
from pathlib import Path

import chess

SEED = 1201
NEED = 300
TARGETS = (8, 15, 22, 29, 36)
rng = random.Random(SEED)
kept = []
started = 0
dropped = 0
while len(kept) < NEED:
    started += 1
    board = chess.Board()
    samples = []
    ended = False
    for ply in range(1, TARGETS[-1] + 1):
        if board.is_game_over(claim_draw=True):
            ended = True
            break
        move = rng.choice(list(board.legal_moves))
        board.push(move)
        if ply in TARGETS:
            if board.is_game_over(claim_draw=True):
                ended = True
                break
            samples.append(board.fen())
    if ended or len(samples) != len(TARGETS):
        dropped += 1
        continue
    kept.extend(samples)
kept = kept[:NEED]
out = Path(__file__).resolve().parent / "R.fens"
out.write_text("\n".join(kept) + "\n")
print(f"seed {SEED}")
print(f"games_started {started}")
print(f"games_dropped {dropped}")
print(f"games_kept {started - dropped}")
print(f"positions {len(kept)}")
print(f"wrote {out}")
