#!/usr/bin/env python3
"""Random legal games. SEED = seat * 100 + 1. Drop a game that ends.

Take one position every 7 plies after ply 8 (plies 15, 22, 29, ...).
A game that is over before ply 71 is dropped and contributes nothing.
"""
import random
import sys
from pathlib import Path

import chess


def main() -> None:
    seat = int(sys.argv[1])
    count = int(sys.argv[2])
    out = Path(sys.argv[3])
    seed = seat * 100 + 1
    rng = random.Random(seed)
    positions: list[str] = []
    kept = 0
    dropped = 0
    while len(positions) < count:
        board = chess.Board()
        sample: list[str] = []
        ended = False
        for ply in range(1, 72):
            if board.is_game_over(claim_draw=True):
                ended = True
                break
            board.push(rng.choice(list(board.legal_moves)))
            if ply > 8 and (ply - 8) % 7 == 0:
                sample.append(board.fen())
        if ended or len(sample) < 8:
            dropped += 1
            continue
        kept += 1
        positions.extend(sample)
    positions = positions[:count]
    out.write_text("\n".join(positions) + "\n")
    print(f"seed {seed}")
    print(f"kept_games {kept}")
    print(f"dropped_games {dropped}")
    print(f"positions {len(positions)}")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
