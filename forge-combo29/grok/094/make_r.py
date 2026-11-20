#!/usr/bin/env python3
"""Random legal games with SEED. Keep a position every 7 plies from ply 8. Drop a game that ends."""

import random
from pathlib import Path

import chess

SEED = 94 * 100 + 1
TARGET = 300
# Positions at ply 8, 15, 22, ... up to this ply. A game that ends sooner is dropped.
LAST_PLY = 8 + 7 * 12


def main() -> None:
    rng = random.Random(SEED)
    kept: list[str] = []
    played = 0
    dropped = 0
    while len(kept) < TARGET:
        played += 1
        board = chess.Board()
        sample: list[str] = []
        ended = False
        for ply in range(1, LAST_PLY + 1):
            moves = list(board.legal_moves)
            if not moves or board.is_game_over(claim_draw=True):
                ended = True
                break
            board.push(rng.choice(moves))
            if ply >= 8 and (ply - 8) % 7 == 0:
                sample.append(board.fen())
            if board.is_game_over(claim_draw=True):
                ended = True
                break
        if ended or board.ply() < LAST_PLY:
            dropped += 1
            continue
        kept.extend(sample)
    kept = kept[:TARGET]
    out = Path("/agent/repos/dwqww/forge-combo29/grok/094/R_positions.epd")
    out.write_text("\n".join(kept) + "\n")
    print(f"seed {SEED} played {played} dropped {dropped} kept {len(kept)} file {out}")


if __name__ == "__main__":
    main()
