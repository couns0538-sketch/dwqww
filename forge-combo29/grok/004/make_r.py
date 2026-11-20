#!/usr/bin/env python3
"""Random legal games. Seed, seed+1, ... One position every 7 plies from ply 8.
A game that ends before the ply cap is dropped, samples and all.
"""
import random
import sys
from pathlib import Path

import chess

SEED = 401
NEED = 300
MAX_PLY = 64


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("usage: make_r.py out.epd")
    out = Path(sys.argv[1])
    positions: list[str] = []
    used = 0
    dropped = 0
    index = 0
    while len(positions) < NEED:
        rng = random.Random(SEED + index)
        index += 1
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
        if ended or not samples:
            dropped += 1
            continue
        used += 1
        positions.extend(samples)
    positions = positions[:NEED]
    out.write_text("".join(fen + "\n" for fen in positions))
    print(f"seed {SEED} games_used {used} games_dropped {dropped} positions {len(positions)} tries {index}")


if __name__ == "__main__":
    main()
