#!/usr/bin/env python3
"""S02 cycle item 2(c): the R position set for the job-1 re-run, seed 211 (SEED + 10).

Random legal games played by python-chess, one position taken every 7 plies, exactly as the brief defines R.
Written to a file before use.
"""
import json
import sys

import chess

SEED = 211
GAMES = int(sys.argv[2]) if len(sys.argv) > 2 else 60
PLIES = 120
EVERY = 7
out = sys.argv[1] if len(sys.argv) > 1 else "R_seed211.fens"

fens = []
meta = []
for g in range(GAMES):
    # a per-game seed derived from SEED so the whole set is reproducible from SEED alone
    import random
    rng = random.Random(SEED * 1000 + g)
    board = chess.Board()
    for ply in range(PLIES):
        moves = list(board.legal_moves)
        if not moves or board.is_game_over():
            break
        board.push(rng.choice(moves))
        if (ply + 1) % EVERY == 0 and not board.is_game_over():
            fens.append(board.fen())
            meta.append({"game": g, "ply": ply + 1})

with open(out, "w") as fh:
    for f in fens:
        fh.write(f + "\n")
with open(out + ".meta.json", "w") as fh:
    json.dump({"seed": SEED, "games": GAMES, "plies_per_game": PLIES, "every": EVERY,
               "positions": len(fens), "first_fens": fens[:3]}, fh, indent=1)
print("wrote %d positions to %s (seed %d)" % (len(fens), out, SEED))
