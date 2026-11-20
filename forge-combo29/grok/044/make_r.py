#!/usr/bin/env python3
"""Random legal games with python-chess. SEED = seat * 100 + 1.

A game that ends (checkmate, stalemate, insufficient material, threefold
repetition, fifty-move rule, or no legal move) before ply 80 is dropped.
From a game that reaches ply 80 still going, keep the position every 7 plies
after ply 8: plies 15, 22, 29, 36, 43, 50, 57, 64, 71, 78.
"""

import random
import sys
from pathlib import Path

import chess

SEED = 4401
MAX_PLY = 80
FIRST_AFTER = 8
STEP = 7
TARGET = 300


def main():
    folder = Path(__file__).resolve().parent
    rng = random.Random(SEED)
    kept = []
    used = 0
    dropped = 0
    while len(kept) < TARGET:
        board = chess.Board()
        samples = []
        ended = False
        for ply in range(1, MAX_PLY + 1):
            if board.is_game_over(claim_draw=True):
                ended = True
                break
            moves = list(board.legal_moves)
            if not moves:
                ended = True
                break
            board.push(rng.choice(moves))
            if ply > FIRST_AFTER and (ply - FIRST_AFTER) % STEP == 0:
                samples.append(board.fen())
        if ended or board.is_game_over(claim_draw=True):
            dropped += 1
            continue
        used += 1
        kept.extend(samples)
    kept = kept[:TARGET]
    (folder / "R.epd").write_text("\n".join(kept) + "\n", encoding="utf-8")
    note = "\n".join([
        f"seed {SEED}",
        f"games_kept {used}",
        f"games_dropped {dropped}",
        f"positions {len(kept)}",
        "plies 15 22 29 36 43 50 57 64 71 78",
        "rule games that end before ply 80 are dropped",
    ])
    (folder / "R_meta.txt").write_text(note + "\n", encoding="utf-8")
    print(note)
    return 0


if __name__ == "__main__":
    sys.exit(main())
