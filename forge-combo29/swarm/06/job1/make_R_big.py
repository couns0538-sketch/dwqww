#!/usr/bin/env python3
"""Make a large random position set from SEED: independent games, one position per 5 plies,
including the game-result end states only when legal. Used to widen the mirror check."""
import random
import sys

import chess

seed, count, out = int(sys.argv[1]), int(sys.argv[2]), sys.argv[3]
rng = random.Random(seed)
fens = []
games = 0
while len(fens) < count:
    games += 1
    board = chess.Board()
    ply = 0
    while not board.is_game_over(claim_draw=False) and ply < 300 and len(fens) < count:
        if ply % 5 == 0:
            fens.append(board.fen())
        moves = list(board.legal_moves)
        if not moves:
            break
        board.push(rng.choice(moves))
        ply += 1
with open(out, "w") as fh:
    for f in fens:
        fh.write(f + "\n")
print("games=%d fens=%d" % (games, len(fens)))
