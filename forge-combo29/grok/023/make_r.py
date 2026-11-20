#!/usr/bin/env python3
"""Random legal games from python-chess. SEED = seat * 100 + 1.

One position every 7 plies after ply 8 (plies 8, 15, 22, ...).
A game that ends before ply 60 is dropped and none of its positions are kept.
"""
import random
import sys
from pathlib import Path

import chess

SEED = 2301
MAX_PLY = 60
NEED = 300
SAMPLES = list(range(8, MAX_PLY, 7))


def main() -> int:
    out = Path(sys.argv[1])
    rng = random.Random(SEED)
    kept = []
    games_kept = 0
    games_dropped = 0
    while len(kept) < NEED:
        board = chess.Board()
        snaps = []
        ended = False
        for ply in range(1, MAX_PLY + 1):
            if board.is_game_over(claim_draw=True):
                ended = True
                break
            move = rng.choice(list(board.legal_moves))
            board.push(move)
            if ply in SAMPLES:
                snaps.append(board.fen())
        if ended or board.is_game_over(claim_draw=True):
            games_dropped += 1
            continue
        games_kept += 1
        for fen in snaps:
            kept.append(fen)
            if len(kept) >= NEED:
                break
    text = "\n".join(kept) + "\n"
    out.write_text(text, encoding="utf-8")
    log = out.with_suffix(".log")
    log.write_text(
        f"seed={SEED}\nmax_ply={MAX_PLY}\nsamples={SAMPLES}\n"
        f"games_kept={games_kept}\ngames_dropped={games_dropped}\n"
        f"positions={len(kept)}\n",
        encoding="utf-8",
    )
    print(log.read_text(), end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
