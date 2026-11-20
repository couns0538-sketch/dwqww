#!/usr/bin/env python3
"""Random legal games from python-chess. SEED = 63 * 100 + 1 = 6301.

A game is kept only if it is still going after 50 plies. Games that end are
dropped. From a kept game, one position is taken every 7 plies after ply 8
(plies 15, 22, 29, 36, 43). Stops at 300 positions.
"""
import pathlib
import random
import chess

SEED = 63 * 100 + 1
rng = random.Random(SEED)
here = pathlib.Path(__file__).resolve().parent
wanted = 300
horizon = 50
sample_plies = [ply for ply in range(15, horizon + 1, 7)]
positions = []
kept = 0
dropped = 0
while len(positions) < wanted:
    board = chess.Board()
    taken = []
    ended = False
    for ply in range(1, horizon + 1):
        if board.is_game_over(claim_draw=True):
            ended = True
            break
        board.push(rng.choice(list(board.legal_moves)))
        if ply in sample_plies:
            taken.append(board.fen())
    if ended or board.is_game_over(claim_draw=True):
        dropped += 1
        continue
    kept += 1
    for fen in taken:
        positions.append(fen)
        if len(positions) >= wanted:
            break
(here / "R.fens").write_text("\n".join(positions) + "\n")
(here / "R.meta").write_text(
    f"seed={SEED}\nkept_games={kept}\ndropped_games={dropped}\n"
    f"positions={len(positions)}\nhorizon={horizon}\nsample_plies={sample_plies}\n"
)
print(f"positions {len(positions)} kept {kept} dropped {dropped}")
