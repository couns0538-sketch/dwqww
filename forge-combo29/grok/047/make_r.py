#!/usr/bin/env python3
"""Random legal games from python-chess. Seed is the seat seed.
A game that ends before ply 80 is dropped. From a game that reaches ply 80,
one position is kept every 7 plies after ply 8 (plies 15, 22, 29, ...).
"""
import random
import sys
import chess

seed = int(sys.argv[1])
out_path = sys.argv[2]
want = int(sys.argv[3]) if len(sys.argv) > 3 else 300
ply_cap = 80
rng = random.Random(seed)

kept_games = 0
dropped = 0
positions = []
while len(positions) < want:
    board = chess.Board()
    ended = False
    while board.ply() < ply_cap:
        if board.is_game_over(claim_draw=True):
            ended = True
            break
        move = rng.choice(list(board.legal_moves))
        board.push(move)
    if ended or board.is_game_over(claim_draw=True) or board.ply() < ply_cap:
        dropped += 1
        continue
    kept_games += 1
    replay = board.copy()
    while replay.ply() > 0:
        replay.pop()
    while replay.ply() < ply_cap:
        move = board.move_stack[replay.ply()]
        replay.push(move)
        ply = replay.ply()
        if ply > 8 and (ply - 8) % 7 == 0:
            positions.append(replay.fen())
            if len(positions) >= want:
                break

with open(out_path, "w") as handle:
    for fen in positions[:want]:
        handle.write(fen + "\n")
print(f"seed {seed}")
print(f"kept_games {kept_games}")
print(f"dropped_games {dropped}")
print(f"positions {min(len(positions), want)}")
print(f"file {out_path}")
