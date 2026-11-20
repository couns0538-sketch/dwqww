#!/usr/bin/env python3
"""Random legal games. SEED 5701.

A game is kept only when it is still going after 64 plies. Games that end on
or before that ply are dropped. One FEN is taken at ply 8 and every 7 plies
after that, through ply 64 (8, 15, ..., 64): nine positions from each kept game.
"""
import random
import chess

SEED = 5701
TARGET = 306
MAX_PLY = 64
rng = random.Random(SEED)
kept = []
dropped = 0
started = 0
while len(kept) < TARGET:
    started += 1
    if started % 20 == 0:
        print(f"progress started {started} dropped {dropped} fens {len(kept)}", flush=True)
    if started > 5000:
        raise SystemExit(f"too many games started {started} dropped {dropped} fens {len(kept)}")
    board = chess.Board()
    sample = []
    alive = True
    for ply in range(1, MAX_PLY + 1):
        if board.is_game_over():
            alive = False
            break
        moves = list(board.legal_moves)
        if not moves:
            alive = False
            break
        board.push(rng.choice(moves))
        if board.is_game_over():
            alive = False
            break
        if ply >= 8 and (ply - 8) % 7 == 0:
            sample.append(board.fen())
    if not alive or not sample:
        dropped += 1
        continue
    kept.extend(sample)
print(f"started {started} dropped {dropped} fens {len(kept)} seed {SEED}")
from pathlib import Path
out = Path(__file__).resolve().parent / "R.fens"
out.write_text("\n".join(kept[:TARGET]) + "\n")
print("wrote", out, "lines", TARGET)
