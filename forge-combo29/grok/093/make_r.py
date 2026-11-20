#!/usr/bin/env python3
"""Random legal games with SEED. One position every 7 plies after ply 8.

A game that ends (no legal move, checkmate, stalemate, insufficient material,
threefold, fifty-move, or a claimed draw) before ply 71 is dropped whole.
Games that are still going at ply 71 contribute plies 15, 22, 29, 36, 43, 50, 57, 64.
"""
import pathlib
import random
import sys

import chess

SEED = 93 * 100 + 1
NEED = int(sys.argv[1]) if len(sys.argv) > 1 else 300
OUT = pathlib.Path(sys.argv[2]) if len(sys.argv) > 2 else pathlib.Path("set_R.epd")
rng = random.Random(SEED)
plies = list(range(15, 72, 7))
fens = []
started = 0
kept = 0
while len(fens) < NEED:
    started += 1
    board = chess.Board()
    samples = []
    ended = False
    for ply in range(1, 72):
        if board.is_game_over(claim_draw=True):
            ended = True
            break
        board.push(rng.choice(list(board.legal_moves)))
        if ply in plies:
            if board.is_game_over(claim_draw=True):
                ended = True
                break
            samples.append(board.fen())
    if ended or len(samples) != len(plies):
        continue
    kept += 1
    fens.extend(samples)
fens = fens[:NEED]
OUT.write_text("".join(fen + "\n" for fen in fens))
print(f"seed {SEED} started {started} kept_games {kept} positions {len(fens)} -> {OUT}")
