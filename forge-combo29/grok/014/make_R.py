#!/usr/bin/env python3
"""Random legal games. SEED, SEED+1, ... one seed per attempt.

A game that ends before ply 80 is dropped. From a game that reaches ply 80,
one position is kept at ply 8, 15, 22, ... (every 7 plies from ply 8).
"""
import random
import sys
from pathlib import Path

import chess

SEED = 1401
TARGET = 300
MAX_PLY = 80
MAX_ATTEMPTS = 8000


def main() -> None:
    out = Path(sys.argv[1])
    kept: list[str] = []
    attempts = 0
    dropped = 0
    while len(kept) < TARGET and attempts < MAX_ATTEMPTS:
        rng = random.Random(SEED + attempts)
        attempts += 1
        board = chess.Board()
        samples: list[str] = []
        ended = False
        for ply in range(1, MAX_PLY + 1):
            if board.is_game_over(claim_draw=True):
                ended = True
                break
            move = rng.choice(list(board.legal_moves))
            board.push(move)
            if ply >= 8 and (ply - 8) % 7 == 0:
                samples.append(board.fen())
        if ended or board.is_game_over(claim_draw=True):
            dropped += 1
            continue
        kept.extend(samples)
    kept = kept[:TARGET]
    out.write_text("\n".join(kept) + "\n")
    print(f"positions {len(kept)} attempts {attempts} dropped {dropped} seed {SEED}")


if __name__ == "__main__":
    main()
