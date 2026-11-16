#!/usr/bin/env python3
"""make_R.py SEED OUT [GAMES] : R position set for seeds — random legal games with python-chess, one position
every 7 plies, written as FENs. Identical rule to the one the brief describes, with this seat's seed.
"""
import random
import sys

import chess

seed = int(sys.argv[1])
out = sys.argv[2]
games = int(sys.argv[3]) if len(sys.argv) > 3 else 400
rng = random.Random(seed)

fens = []
for g in range(games):
    board = chess.Board()
    for ply in range(200):
        if board.is_game_over():
            break
        if ply % 7 == 0:
            fens.append(board.fen())
        moves = list(board.legal_moves)
        board.push(rng.choice(moves))

with open(out, "w") as fh:
    fh.write("\n".join(fens) + "\n")
print("seed %d: %d positions from %d games -> %s" % (seed, len(fens), games, out))
