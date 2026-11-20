#!/usr/bin/env python3
"""Random legal games. Drop a game that ends. Keep one FEN every 7 plies from ply 8."""
import random
import sys

import chess

SEED = 5501
NEED = 300
MAX_PLY = 80
rng = random.Random(SEED)
fens = []
kept = 0
dropped = 0
attempts = 0
while len(fens) < NEED:
    attempts += 1
    board = chess.Board()
    taken = []
    ended = False
    for ply in range(1, MAX_PLY + 1):
        if board.is_game_over(claim_draw=True):
            ended = True
            break
        board.push(rng.choice(list(board.legal_moves)))
        if ply >= 8 and (ply - 8) % 7 == 0:
            taken.append(board.fen())
    if ended or board.is_game_over(claim_draw=True):
        dropped += 1
        continue
    kept += 1
    fens.extend(taken)
fens = fens[:NEED]
out = sys.argv[1]
with open(out, "w") as handle:
    handle.write("\n".join(fens) + "\n")
print(f"seed {SEED} attempts {attempts} kept {kept} dropped {dropped} fens {len(fens)} out {out}")
