#!/usr/bin/env python3
"""Random legal games from python-chess. Generator seed is SEAT*100+1.

One position every 7 plies after ply 8 (plies 15, 22, 29, ...).
A game that ends before ply 80 is dropped. Games that reach ply 80
without a result keep those positions. Writes the first 300 FENs.
"""
import random
import chess

SEED = 3601
rng = random.Random(SEED)
kept_games = 0
dropped = 0
positions = []
while len(positions) < 300:
    board = chess.Board()
    taken = []
    ended = False
    for ply in range(1, 81):
        if board.is_game_over(claim_draw=True):
            ended = True
            break
        move = rng.choice(list(board.legal_moves))
        board.push(move)
        if ply > 8 and (ply - 8) % 7 == 0:
            taken.append(board.fen())
    if ended or len(taken) == 0:
        dropped += 1
        continue
    kept_games += 1
    positions.extend(taken)
positions = positions[:300]
out = __import__("pathlib").Path(__file__).with_name("set_R.epd")
out.write_text("\n".join(positions) + "\n")
print(f"seed {SEED} kept_games {kept_games} dropped {dropped} fens {len(positions)}")
