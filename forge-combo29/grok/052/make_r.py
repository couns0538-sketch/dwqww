#!/usr/bin/env python3
"""300 positions from random legal games. SEED = seat * 100 + 1.

A game that ends is dropped, including any sample taken from it.
Games that reach ply 64 without ending contribute the position every 7 plies
after ply 8 (8, 15, 22, 29, 36, 43, 50, 57).
"""
import pathlib
import random

import chess

SEAT = int(pathlib.Path.home().joinpath("grok_seat.txt").read_text().strip())
SEED = SEAT * 100 + 1
rng = random.Random(SEED)
wanted = 300
kept = []
games = 0
dropped = 0
while len(kept) < wanted:
    board = chess.Board()
    samples = []
    ended = False
    for ply in range(1, 65):
        if board.is_game_over(claim_draw=True):
            ended = True
            break
        board.push(rng.choice(list(board.legal_moves)))
        if ply >= 8 and (ply - 8) % 7 == 0:
            samples.append(board.fen())
    games += 1
    if ended or board.is_game_over(claim_draw=True):
        dropped += 1
        continue
    kept.extend(samples)
kept = kept[:wanted]
repo = pathlib.Path(pathlib.Path.home().joinpath("grok_repo.txt").read_text().strip())
out = repo / "forge-combo29" / "grok" / f"{SEAT:03d}" / "set_R.epd"
out.write_text("\n".join(kept) + "\n")
print(f"seed {SEED} games {games} dropped {dropped} positions {len(kept)} file {out}")
