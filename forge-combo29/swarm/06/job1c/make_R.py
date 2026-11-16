#!/usr/bin/env python3
"""Make the R position set: random legal games played by python-chess, SEED from argv,
one position taken every 7 plies. Writes FENs, one per line."""
import random
import sys

import chess

seed = int(sys.argv[1])
count = int(sys.argv[2])
out = sys.argv[3]

rng = random.Random(seed)
fens = []
games = 0
while len(fens) < count:
    games += 1
    board = chess.Board()
    ply = 0
    while not board.is_game_over(claim_draw=False) and ply < 400:
        if ply % 7 == 0 and ply > 0 and len(fens) < count:
            fens.append(board.fen())
        moves = list(board.legal_moves)
        if not moves:
            break
        board.push(rng.choice(moves))
        ply += 1
    if games > 40 and len(fens) < count:
        break

with open(out, "w") as fh:
    for fen in fens:
        fh.write(fen + "\n")
print(f"games={games} fens={len(fens)} seed={seed}")
