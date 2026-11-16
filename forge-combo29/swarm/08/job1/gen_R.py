#!/usr/bin/env python3
"""gen_R.py SEED COUNT OUT — random legal games, one position every 7 plies, FEN per line."""
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
    while not board.is_game_over(claim_draw=False):
        moves = list(board.legal_moves)
        if not moves:
            break
        if ply % 7 == 0 and len(fens) < count:
            fens.append(board.fen())
        board.push(rng.choice(moves))
        ply += 1
        if ply > 500:
            break

with open(out, "w") as fh:
    for f in fens:
        fh.write(f + "\n")
sys.stderr.write("games %d, positions %d, seed %d\n" % (games, len(fens), seed))
