#!/usr/bin/env python3
"""Random legal games from python-chess.

Seed is 501 (seat 005). One stream, random.Random(501).
A position is kept at ply 8, 15, 22, ... A game that ends before the
last sample ply is dropped, including every sample taken from it.
Stops at 300 positions.
"""
from __future__ import annotations

import random
from pathlib import Path

import chess

SEED = 501
WANT = 300
# Ten samples: ply 8 then every 7 plies, through ply 71.
SAMPLE_PLIES = list(range(8, 8 + 7 * 10, 7))


def main() -> None:
    rng = random.Random(SEED)
    kept: list[str] = []
    played = 0
    dropped = 0
    while len(kept) < WANT:
        board = chess.Board()
        samples: list[str] = []
        ended = False
        for ply in range(1, SAMPLE_PLIES[-1] + 1):
            if board.is_game_over(claim_draw=True):
                ended = True
                break
            board.push(rng.choice(list(board.legal_moves)))
            if ply in SAMPLE_PLIES:
                samples.append(board.fen())
        played += 1
        if ended or len(samples) != len(SAMPLE_PLIES) or board.is_game_over(claim_draw=True):
            dropped += 1
            continue
        kept.extend(samples)
    kept = kept[:WANT]
    out = Path(__file__).with_name("openings_R.epd")
    out.write_text("\n".join(kept) + "\n")
    print(f"games_played {played}")
    print(f"games_dropped {dropped}")
    print(f"positions {len(kept)}")
    print(f"seed {SEED}")
    print(f"sample_plies {' '.join(str(p) for p in SAMPLE_PLIES)}")
    print(f"file {out}")


if __name__ == "__main__":
    main()
