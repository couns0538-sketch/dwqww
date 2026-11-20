#!/usr/bin/env python3
"""Random legal games with a fixed seed.

One position every 7 plies starting at ply 8 (8, 15, 22, ...).
A game that ends before ply 8 is dropped. The terminal position of a
finished game is not kept: the sample is the position about to be played,
and only while the game is still going.
"""
import random
import sys
import chess

seed = int(sys.argv[1])
need = int(sys.argv[2])
out_path = sys.argv[3]
rng = random.Random(seed)
fens = []
games = 0
dropped = 0
while len(fens) < need:
    board = chess.Board()
    ply = 0
    kept_this = 0
    while not board.is_game_over(claim_draw=True) and ply < 400:
        if ply >= 8 and (ply - 8) % 7 == 0:
            fens.append(board.fen())
            kept_this += 1
            if len(fens) >= need:
                break
        moves = list(board.legal_moves)
        board.push(moves[rng.randrange(len(moves))])
        ply += 1
    games += 1
    if kept_this == 0:
        dropped += 1
with open(out_path, "w", encoding="utf-8") as handle:
    for fen in fens:
        handle.write(fen + "\n")
print("games", games, "dropped_before_ply8", dropped, "positions", len(fens), "seed", seed)
