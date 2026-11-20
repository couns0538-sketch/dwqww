#!/usr/bin/env python3
"""Random legal games from python-chess. SEED = seat * 100 + 1.

A game is kept only when it is still not over after 80 plies. Games that end
before that are dropped. From a kept game, one position is taken at ply 8 and
every 7 plies after that. The first 300 positions are written.
"""
import random
from pathlib import Path

import chess

SEAT = int(Path("/home/ubuntu/grok_seat.txt").read_text().strip())
SEED = SEAT * 100 + 1
WANT = 300
HORIZON = 80
rng = random.Random(SEED)
positions = []
kept = 0
dropped = 0
while len(positions) < WANT:
    board = chess.Board()
    fens = []
    ended = False
    for _ply in range(HORIZON):
        if board.is_game_over(claim_draw=True):
            ended = True
            break
        moves = list(board.legal_moves)
        if not moves:
            ended = True
            break
        board.push(rng.choice(moves))
        fens.append(board.fen())
    if ended or len(fens) < HORIZON:
        dropped += 1
        continue
    kept += 1
    for ply in range(8, HORIZON + 1, 7):
        positions.append(fens[ply - 1])
        if len(positions) >= WANT:
            break

folder = Path("forge-combo29/grok") / f"{SEAT:03d}"
(folder / "R.epd").write_text("\n".join(positions) + "\n", encoding="utf-8")
(folder / "R.meta").write_text(
    f"seed {SEED}\nhorizon {HORIZON}\nkept_games {kept}\ndropped_games {dropped}\npositions {len(positions)}\n",
    encoding="utf-8",
)
print(f"seed {SEED} kept {kept} dropped {dropped} positions {len(positions)}")
