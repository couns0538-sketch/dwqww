#!/usr/bin/env python3
"""300 positions. Each random draw uses the next seed, starting at 8201.

A game that ends before ply 36 is dropped whole. From a game that reaches
ply 36, the positions after plies 8, 15, 22, 29 and 36 are kept.
"""
import random
import chess
import os

SEED0 = 82 * 100 + 1
seed = SEED0


def draw_move(board):
    global seed
    rng = random.Random(seed)
    seed += 1
    return rng.choice(list(board.legal_moves))


want = 300
positions = []
used = 0
dropped = 0
while len(positions) < want:
    board = chess.Board()
    samples = []
    ended = False
    for ply in range(1, 37):
        if board.is_game_over(claim_draw=True):
            ended = True
            break
        board.push(draw_move(board))
        if ply >= 8 and (ply - 8) % 7 == 0:
            if board.is_game_over(claim_draw=True):
                ended = True
                break
            samples.append(board.fen())
    if ended or len(samples) != 5:
        dropped += 1
        continue
    used += 1
    positions.extend(samples)

positions = positions[:want]
here = os.path.dirname(os.path.abspath(__file__))
open(os.path.join(here, "R.fens"), "w").write("\n".join(positions) + "\n")
note = (
    f"seed_start={SEED0}\n"
    f"next_seed_after={seed}\n"
    "rule=each legal-move draw uses random.Random(seed) then seed += 1\n"
    "sample_plies=8,15,22,29,36\n"
    f"games_kept={used}\n"
    f"games_dropped={dropped}\n"
    f"positions={len(positions)}\n"
    "games_that_end_before_ply_36_are_dropped=yes\n"
)
open(os.path.join(here, "R.meta"), "w").write(note)
print(note)
