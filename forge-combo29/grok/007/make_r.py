#!/usr/bin/env python3
"""Random legal positions for set R.

SEED = seat * 100 + 1. Play games with python-chess. A game that ends
(checkmate, stalemate, insufficient material, or a claimable draw) before
ply 80 is dropped. From a game that is still going at ply 80, keep the
position after ply 8 and then every 7 plies: 8, 15, 22, ..., 78.
"""
import random
import sys
from pathlib import Path

import chess

SEED = 701
TARGET = 300
MAX_PLY = 80


def main() -> int:
    out = Path(sys.argv[1])
    rng = random.Random(SEED)
    kept: list[str] = []
    started = 0
    dropped = 0
    while len(kept) < TARGET:
        started += 1
        board = chess.Board()
        sample: list[str] = []
        ended = False
        for ply in range(1, MAX_PLY + 1):
            if board.is_game_over(claim_draw=True):
                ended = True
                break
            move = rng.choice(list(board.legal_moves))
            board.push(move)
            if ply >= 8 and (ply - 8) % 7 == 0:
                sample.append(board.fen())
        if ended or len(sample) == 0:
            dropped += 1
            continue
        kept.extend(sample)
    kept = kept[:TARGET]
    out.write_text("\n".join(kept) + "\n")
    print(f"seed {SEED} games_started {started} games_dropped {dropped} positions {len(kept)} file {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
