#!/usr/bin/env python3
"""Generate the R position set for seat 13 area 3 job 1.

Random legal games played by python-chess, SEED from the seat (1301),
one position taken every 7 plies. Usage: gen_R.py SEED N_OUT OUT_FILE
"""
import random
import sys

import chess

SEED = int(sys.argv[1])
N_OUT = int(sys.argv[2])
OUT = sys.argv[3]

rng = random.Random(SEED)
fens = []
games = 0
while len(fens) < N_OUT:
    games += 1
    board = chess.Board()
    ply = 0
    while board.legal_moves and not board.is_game_over(claim_draw=False) and ply < 400:
        if ply % 7 == 0 and len(fens) < N_OUT:
            fens.append(board.fen())
        moves = list(board.legal_moves)
        board.push(rng.choice(moves))
        ply += 1
    if games > 20000:
        sys.exit("too many games, aborting")

with open(OUT, "w") as f:
    for fen in fens:
        f.write(fen + "\n")
print(f"seed {SEED} games {games} positions {len(fens)} -> {OUT}")
