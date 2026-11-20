#!/usr/bin/env python3
"""Random legal games. SEED = seat * 100 + 1. Drop a game that ends. Keep a FEN every 7 plies from ply 8."""
import random
import sys
import chess

seat = int(sys.argv[1])
count = int(sys.argv[2])
seed = seat * 100 + 1
rng = random.Random(seed)
out = []
kept = 0
dropped = 0
game_plies = 64
while len(out) < count:
    board = chess.Board()
    ended = False
    snapshots = []
    for ply in range(game_plies):
        if board.is_game_over(claim_draw=True):
            ended = True
            break
        board.push(rng.choice(list(board.legal_moves)))
        played = ply + 1
        if played >= 8 and (played - 8) % 7 == 0:
            snapshots.append(board.fen())
    if ended or board.is_game_over(claim_draw=True):
        dropped += 1
        continue
    kept += 1
    out.extend(snapshots)
text = "".join(fen + "\n" for fen in out[:count])
sys.stdout.write(text)
print(f"SEED {seed} kept {kept} dropped {dropped} pool {len(out)} written {count}", file=sys.stderr)
