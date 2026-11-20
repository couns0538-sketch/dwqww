#!/usr/bin/env python3
"""Random legal positions. Seed 7801. One sample every 7 plies after ply 8.

A game that reaches a terminal result (including threefold and the 50-move
rule) is dropped, samples included. Games still going at ply 80 are kept.
"""
import random
from pathlib import Path

import chess

SEED = 7801
WANT = 300
MAX_PLY = 80
rng = random.Random(SEED)
kept = []
started = 0
dropped = 0
while len(kept) < WANT:
    board = chess.Board()
    started += 1
    samples = []
    ply = 0
    while ply < MAX_PLY and not board.is_game_over(claim_draw=True):
        board.push(rng.choice(list(board.legal_moves)))
        ply += 1
        if ply >= 8 and (ply - 8) % 7 == 0 and not board.is_game_over(claim_draw=True):
            samples.append(board.fen())
    if board.is_game_over(claim_draw=True):
        dropped += 1
        continue
    kept.extend(samples)
kept = kept[:WANT]
out = Path(__file__).resolve().parent / "R.fens"
out.write_text("\n".join(kept) + "\n")
print(f"positions {len(kept)}")
print(f"games_started {started}")
print(f"games_dropped {dropped}")
print(f"games_kept {started - dropped}")
print(f"seed {SEED}")
print(f"wrote {out}")
