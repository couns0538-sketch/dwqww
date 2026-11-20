#!/usr/bin/env python3
"""Random legal games with python-chess.

Seat seed is 7601. Game i is played with random.Random(7601 + i).
A game that ends (checkmate, stalemate, insufficient material, threefold,
fifty-move, or no legal move) before ply 78 is dropped.
From a game that is still going at ply 78, keep the positions at plies
15, 22, 29, 36, 43, 50, 57, 64, 71 (every 7 plies, strictly after ply 8).
"""
import random
import sys
import chess

SEED = 7601
TARGET = int(sys.argv[1])
out_path = sys.argv[2]
kept = []
game = 0
dropped = 0
while len(kept) < TARGET:
    rng = random.Random(SEED + game)
    board = chess.Board()
    samples = []
    ended = False
    for ply in range(1, 79):
        moves = list(board.legal_moves)
        if not moves or board.is_game_over(claim_draw=True):
            ended = True
            break
        board.push(rng.choice(moves))
        if ply >= 15 and (ply - 15) % 7 == 0:
            samples.append(board.fen())
        if board.is_game_over(claim_draw=True):
            ended = True
            break
    if ended or len(samples) < 9:
        dropped += 1
    else:
        kept.extend(samples)
    game += 1
    if game > 20000:
        raise SystemExit("too many games")
kept = kept[:TARGET]
with open(out_path, "w") as handle:
    for fen in kept:
        handle.write(fen + "\n")
print("games_started", game)
print("games_dropped", dropped)
print("positions", len(kept))
print("first_seed", SEED)
print("last_seed", SEED + game - 1)
