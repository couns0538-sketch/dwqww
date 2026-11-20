#!/usr/bin/env python3
"""Build set_R.epd from random legal games.

SEED = seat * 100 + 1. Each game is a random legal play from the start
position. A game that ends (checkmate, stalemate, insufficient material,
seventy-five moves, or fivefold repetition) before ply 80 is dropped, including
any positions already seen in it. A game still going at ply 80 contributes the
position after every ply p where p > 8 and (p - 8) is a multiple of 7
(15, 22, 29, ...). The file keeps the first 300 of those positions.
"""
import random
import chess

SEED = 69 * 100 + 1
NEED = 300
CAP = 80
rng = random.Random(SEED)
kept = []
started = 0
dropped = 0
while len(kept) < NEED:
    started += 1
    board = chess.Board()
    samples = []
    ended = False
    for ply in range(1, CAP + 1):
        if board.is_game_over():
            ended = True
            break
        move = rng.choice(list(board.legal_moves))
        board.push(move)
        if ply > 8 and (ply - 8) % 7 == 0:
            samples.append(board.fen())
        if board.is_game_over():
            ended = True
            break
    if ended or len(samples) == 0:
        dropped += 1
        continue
    kept.extend(samples)

kept = kept[:NEED]
out = __file__.replace("make_r.py", "set_R.epd")
log = __file__.replace("make_r.py", "set_R.log")
with open(out, "w", encoding="utf-8") as handle:
    handle.write("\n".join(kept) + "\n")
with open(log, "w", encoding="utf-8") as handle:
    handle.write(
        f"seed\t{SEED}\nstarted\t{started}\ndropped\t{dropped}\nkept_games\t{started - dropped}\npositions\t{len(kept)}\ncap_ply\t{CAP}\n"
    )
print(open(log, encoding="utf-8").read(), end="")
