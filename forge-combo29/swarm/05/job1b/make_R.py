#!/usr/bin/env python3
"""make_R.py -- builds the R position set (the brief's third set: random legal games, one position every 7 plies).
Seed is taken from argv so the job1 repeat uses SEED + 10 = 511 while the first run used 501.
Writes positions/R_seed<N>.fens and, with --mirror, R_seed<N>_mirror.fens.
"""
import random
import sys

import chess

seed = int(sys.argv[1]) if len(sys.argv) > 1 else 511
count = int(sys.argv[2]) if len(sys.argv) > 2 else 200
R = random.Random(seed)

fens = []
seen = set()
games = 0
while len(fens) < count and games < 4000:
    games += 1
    b = chess.Board()
    ply = 0
    while not b.is_game_over(claim_draw=False) and ply < 300:
        legal = list(b.legal_moves)
        if not legal:
            break
        b.push(R.choice(legal))
        ply += 1
        if ply % 7 == 0 and not b.is_game_over(claim_draw=False):
            key = b.fen()
            if key in seen:
                continue
            seen.add(key)
            fens.append(key)
            if len(fens) >= count:
                break

path = f"positions/R_seed{seed}.fens"
with open(path, "w") as f:
    for x in fens:
        f.write(x + "\n")
print(f"seed {seed}: wrote {len(fens)} positions to {path} (from {games} games)")
# sanity: every FEN must be legal for python-chess and not terminal
bad = 0
for x in fens:
    b = chess.Board(x)
    if not b.is_valid() or b.is_game_over(claim_draw=False):
        bad += 1
print(f"positions that are illegal or already over: {bad} (must be 0)")
