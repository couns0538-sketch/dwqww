#!/usr/bin/env python3
"""Random legal games. SEED = seat * 100 + 1.

A position is kept every 7 plies from ply 8 onward while the game is not over.
The terminal position is not kept. A game that ends before ply 8 adds nothing.
"""
import random
import sys
from pathlib import Path

import chess

seed = int(sys.argv[1])
count = int(sys.argv[2])
out = Path(sys.argv[3])
rng = random.Random(seed)
kept: list[str] = []
games = 0
dropped_early = 0
while len(kept) < count:
    games += 1
    board = chess.Board()
    ply = 0
    took = False
    while not board.is_game_over():
        board.push(rng.choice(list(board.legal_moves)))
        ply += 1
        if ply >= 8 and (ply - 8) % 7 == 0 and not board.is_game_over():
            kept.append(board.fen())
            took = True
            if len(kept) >= count:
                break
        if ply >= 120:
            break
    if not took:
        dropped_early += 1
out.write_text("\n".join(kept) + "\n")
print(f"seed {seed}")
print(f"positions {len(kept)}")
print(f"games_started {games}")
print(f"games_dropped_before_ply8 {dropped_early}")
