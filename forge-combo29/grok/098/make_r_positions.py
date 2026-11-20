#!/usr/bin/env python3
"""Random legal games with SEED = seat * 100 + 1.

One position every 7 plies after ply 8 (plies 8, 15, 22, ...).
A game that ends before ply 64 is dropped, including positions already taken from it.
"""
import os
import random
import sys

import chess

seat = int(open(os.path.expanduser("~/grok_seat.txt")).read().strip())
seed = seat * 100 + 1
need = int(sys.argv[1]) if len(sys.argv) > 1 else 300
out = sys.argv[2]
rng = random.Random(seed)
kept = []
used = 0
dropped = 0
while len(kept) < need:
    board = chess.Board()
    taken = []
    ended = False
    ply = 0
    while ply < 64:
        if board.is_game_over(claim_draw=True):
            ended = True
            break
        moves = list(board.legal_moves)
        if not moves:
            ended = True
            break
        board.push(rng.choice(moves))
        ply += 1
        if ply >= 8 and (ply - 8) % 7 == 0:
            taken.append(board.fen())
    if ended or ply < 64 or not taken:
        dropped += 1
        continue
    used += 1
    kept.extend(taken)
kept = kept[:need]
with open(out, "w") as handle:
    for fen in kept:
        handle.write(fen + "\n")
meta = out + ".meta"
with open(meta, "w") as handle:
    handle.write(f"seed={seed}\n")
    handle.write(f"seat={seat}\n")
    handle.write(f"games_kept={used}\n")
    handle.write(f"games_dropped={dropped}\n")
    handle.write(f"positions={len(kept)}\n")
    handle.write("rule=ply 8 then every 7 plies; drop a game that ends before ply 64\n")
print(f"seed={seed} kept_games={used} dropped_games={dropped} positions={len(kept)}")
