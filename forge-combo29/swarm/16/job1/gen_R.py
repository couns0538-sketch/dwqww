#!/usr/bin/env python3
"""gen_R.py SEED COUNT OUTFILE : random legal games, one position every 7 plies."""
import random
import sys

import chess

seed = int(sys.argv[1])
count = int(sys.argv[2])
out = sys.argv[3]
rng = random.Random(seed)
fens = []
game = 0
while len(fens) < count:
    game += 1
    board = chess.Board()
    ply = 0
    while len(fens) < count and not board.is_game_over(claim_draw=False) and ply < 400:
        moves = list(board.legal_moves)
        if not moves:
            break
        board.push(rng.choice(moves))
        ply += 1
        if ply % 7 == 0:
            fens.append(board.fen())
with open(out, "w") as fh:
    for f in fens:
        fh.write(f + "\n")
print("games", game, "positions", len(fens), "file", out)
