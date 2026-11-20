#!/usr/bin/env python3
"""Random legal positions. SEED games. Drop a game that ends before ply 80.

Take one position every 7 plies after ply 8: 15, 22, 29, 36, 43, 50, 57, 64, 71, 78.
"""
import random
import sys

import chess

SEED = 3901
NEED = int(sys.argv[1]) if len(sys.argv) > 1 else 300
CAP = 80
SAMPLES = list(range(15, CAP, 7))
rng = random.Random(SEED)
kept = []
games = 0
dropped = 0
while len(kept) < NEED:
    games += 1
    board = chess.Board()
    positions = []
    ended = False
    for ply in range(1, CAP + 1):
        moves = list(board.legal_moves)
        if not moves or board.is_game_over(claim_draw=False):
            ended = True
            break
        board.push(rng.choice(moves))
        if ply in SAMPLES:
            positions.append(board.fen())
        if board.is_game_over(claim_draw=False):
            ended = True
            break
    if ended or len(positions) != len(SAMPLES):
        dropped += 1
        continue
    kept.extend(positions)
print(f"games {games} dropped {dropped} positions {len(kept)}", file=sys.stderr)
sys.stdout.write("\n".join(kept[:NEED]) + "\n")
