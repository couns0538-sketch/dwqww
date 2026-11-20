#!/usr/bin/env python3
"""Random legal games with SEED. Sample ply 8, 15, 22, ... Drop a game that ends."""
import random
import sys

import chess

SEED = 4501
WANT = int(sys.argv[1]) if len(sys.argv) > 1 else 300
MAX_PLY = 80
OUT = sys.argv[2]

rng = random.Random(SEED)
kept = []
games_kept = 0
games_dropped = 0
attempts = 0
while len(kept) < WANT and attempts < 50000:
    attempts += 1
    board = chess.Board()
    samples = []
    ended = False
    for _ply in range(MAX_PLY):
        if board.is_game_over(claim_draw=True):
            ended = True
            break
        moves = list(board.legal_moves)
        if not moves:
            ended = True
            break
        board.push(rng.choice(moves))
        played = board.ply()
        if played >= 8 and (played - 8) % 7 == 0:
            samples.append(board.fen())
    if ended or board.is_game_over(claim_draw=True):
        games_dropped += 1
        continue
    games_kept += 1
    kept.extend(samples)

if len(kept) < WANT:
    raise SystemExit(f"only {len(kept)} positions after {attempts} games")

kept = kept[:WANT]
with open(OUT, "w") as handle:
    handle.write("\n".join(kept) + "\n")
print("positions", len(kept))
print("games_kept", games_kept)
print("games_dropped", games_dropped)
print("attempts", attempts)
print("seed", SEED)
print("out", OUT)
