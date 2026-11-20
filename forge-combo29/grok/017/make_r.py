#!/usr/bin/env python3
"""Random legal games. Seed is the seat seed. Games that end are dropped.

A game is kept only when it is still going after ply 78. Positions are the
boards after plies 15, 22, 29, 36, 43, 50, 57, 64, 71 and 78: every 7 plies
after ply 8.
"""
import random
import sys

import chess

seed = int(sys.argv[1])
want = int(sys.argv[2])
out_path = sys.argv[3]
rng = random.Random(seed)
sample_plies = list(range(15, 79, 7))
kept = []
started = 0
dropped = 0
while len(kept) < want:
    started += 1
    board = chess.Board()
    snapshots = {}
    ended = False
    while board.ply() < 80:
        if board.is_game_over(claim_draw=True):
            ended = True
            break
        board.push(rng.choice(list(board.legal_moves)))
        if board.ply() in sample_plies:
            snapshots[board.ply()] = board.fen()
        if board.is_game_over(claim_draw=True):
            ended = True
            break
    if ended or any(ply not in snapshots for ply in sample_plies):
        dropped += 1
        continue
    for ply in sample_plies:
        kept.append(snapshots[ply])
        if len(kept) >= want:
            break

with open(out_path, "w", encoding="utf-8") as handle:
    for fen in kept[:want]:
        handle.write(fen + "\n")
print(f"seed {seed} started {started} dropped {dropped} kept {min(want, len(kept))} file {out_path}")
