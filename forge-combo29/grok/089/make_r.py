#!/usr/bin/env python3
"""Random legal games. SEED = seat * 100 + 1.

Play until ply 8 + 7 * 4 (ply 36). Keep a FEN every 7 plies from ply 8
(8, 15, 22, 29, 36). If the game ends before ply 36, drop the whole game.
"""
import random
import sys
from pathlib import Path

import chess

seed = int(sys.argv[1])
want = int(sys.argv[2])
out = Path(sys.argv[3])
rng = random.Random(seed)
target_ply = 8 + 7 * 4
kept = []
games = 0
dropped = 0
while len(kept) < want:
    board = chess.Board()
    fens = []
    ended = False
    for ply in range(1, target_ply + 1):
        if board.is_game_over(claim_draw=True):
            ended = True
            break
        move = rng.choice(list(board.legal_moves))
        board.push(move)
        if ply >= 8 and (ply - 8) % 7 == 0:
            fens.append(board.fen())
    games += 1
    if ended or board.is_game_over(claim_draw=True) or len(fens) != 5:
        dropped += 1
        continue
    kept.extend(fens)
kept = kept[:want]
out.write_text("\n".join(kept) + "\n")
print(f"seed={seed} games_tried={games} dropped={dropped} kept={len(kept)} file={out}")
