#!/usr/bin/env python3
"""Random legal games from SEED. Keep a FEN every 7 plies from ply 8. Drop games that end."""
import random
import sys
from pathlib import Path

import chess

SEED = 2201
TARGET = 300
MAX_PLY = 80


def main() -> int:
    rng = random.Random(SEED)
    kept: list[str] = []
    games = 0
    dropped = 0
    while len(kept) < TARGET:
        games += 1
        board = chess.Board()
        sample: list[str] = []
        ended = False
        for ply in range(1, MAX_PLY + 1):
            if board.is_game_over(claim_draw=True):
                ended = True
                break
            move = rng.choice(list(board.legal_moves))
            board.push(move)
            if ply >= 8 and (ply - 8) % 7 == 0 and not board.is_game_over(claim_draw=True):
                sample.append(board.fen())
        if ended or not sample:
            dropped += 1
            continue
        kept.extend(sample)
    kept = kept[:TARGET]
    out = Path(sys.argv[1])
    out.write_text("\n".join(kept) + "\n")
    print(f"games_started {games}")
    print(f"games_dropped {dropped}")
    print(f"positions {len(kept)}")
    print(f"seed {SEED}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
