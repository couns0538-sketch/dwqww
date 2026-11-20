#!/usr/bin/env python3
"""Random legal positions for set R.

SEED is the first argument (seat * 100 + 1). Games are played with
random.Random(SEED). A game that ends (checkmate, stalemate, insufficient
material, threefold, fifty-move, or fivefold) is dropped. A game still going
at ply 80 is kept. From a kept game, one position is taken at ply 8 and then
every 7 plies (8, 15, 22, ...). The first N kept positions are written.
"""
import random
import sys
import chess

seed = int(sys.argv[1])
count = int(sys.argv[2])
out_path = sys.argv[3]
rng = random.Random(seed)
kept = []
games = 0
dropped = 0
while len(kept) < count:
    board = chess.Board()
    games += 1
    ended = False
    positions = []
    while board.ply() < 80:
        if board.is_game_over(claim_draw=True):
            ended = True
            break
        move = rng.choice(list(board.legal_moves))
        board.push(move)
        ply = board.ply()
        if ply >= 8 and (ply - 8) % 7 == 0 and not board.is_game_over(claim_draw=True):
            positions.append(board.fen())
    if ended or board.is_game_over(claim_draw=True):
        dropped += 1
        continue
    kept.extend(positions)
open(out_path, "w").write("\n".join(kept[:count]) + "\n")
print(f"games_started={games} dropped={dropped} kept={count} seed={seed}")
