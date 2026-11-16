#!/usr/bin/env python3
"""make_R.py : write R positions = one position every 7 plies of random legal games.
SEED comes from argv[1] (default 2301). Writes FENs to argv[2] and a sidecar log."""
import random
import sys

import chess

seed = int(sys.argv[1]) if len(sys.argv) > 1 else 2301
out_path = sys.argv[2] if len(sys.argv) > 2 else "R.fens"
want = int(sys.argv[3]) if len(sys.argv) > 3 else 5000
log_path = out_path + ".log"

rng = random.Random(seed)
fens = []
log = []
games = 0
while len(fens) < want:
    games += 1
    board = chess.Board()
    plies = 0
    # a random game of 60..140 plies, taking a position every 7 plies
    target = rng.randint(60, 140)
    while plies < target:
        moves = list(board.legal_moves)
        if not moves:
            break
        board.push(rng.choice(moves))
        plies += 1
        if plies % 7 == 0 and len(fens) < want:
            fens.append(board.fen())
            log.append("%d %d %s" % (games, plies, board.fen()))

with open(out_path, "w") as f:
    for fen in fens:
        f.write(fen + "\n")
with open(log_path, "w") as f:
    f.write("seed %d games %d positions %d\n" % (seed, games, len(fens)))
    for line in log:
        f.write(line + "\n")
print("seed %d games %d positions %d -> %s" % (seed, games, len(fens), out_path))
