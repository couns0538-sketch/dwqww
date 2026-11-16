#!/usr/bin/env python3
"""gen_R.py SEED N OUT : random legal games, one position every 7 plies, FENs to OUT."""
import random, sys, chess

seed = int(sys.argv[1]); n = int(sys.argv[2]); out = sys.argv[3]
rng = random.Random(seed)
fens = []
while len(fens) < n:
    b = chess.Board()
    ply = 0
    while len(fens) < n:
        moves = list(b.legal_moves)
        if not moves or b.is_game_over(claim_draw=False):
            break
        b.push(rng.choice(moves))
        ply += 1
        if ply % 7 == 0:
            fens.append(b.fen(en_passant="fen"))
with open(out, "w") as f:
    for x in fens:
        f.write(x + "\n")
print("wrote", len(fens), "fens seed", seed)
