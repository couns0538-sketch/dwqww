#!/usr/bin/env python3
"""Random legal games with python-chess. SEED = seat * 100 + 1.

A game that ends before ply 80 is dropped. From a game that reaches ply 80
still ongoing, keep a FEN every 7 plies after ply 8 (plies 15, 22, 29, ...).
Write the first 300 of those FENs.
"""
import random
from pathlib import Path

import chess

seat = int(Path("/home/ubuntu/grok_seat.txt").read_text().strip())
seed = seat * 100 + 1
rng = random.Random(seed)
want = 300
max_ply = 80
kept_games = 0
tried = 0
positions = []
while len(positions) < want and tried < 50000:
    tried += 1
    board = chess.Board()
    samples = []
    ended = False
    ply = 0
    while ply < max_ply:
        if board.is_game_over(claim_draw=True):
            ended = True
            break
        moves = list(board.legal_moves)
        board.push(rng.choice(moves))
        ply += 1
        if ply > 8 and (ply - 8) % 7 == 0 and not board.is_game_over(claim_draw=True):
            samples.append(board.fen())
    if ended or ply < max_ply:
        continue
    kept_games += 1
    positions.extend(samples)
positions = positions[:want]
out = Path(__file__).resolve().parent / "R.fen"
out.write_text("\n".join(positions) + "\n")
print(f"seed {seed}")
print(f"tried {tried}")
print(f"kept_games {kept_games}")
print(f"positions {len(positions)}")
print(f"file {out}")
