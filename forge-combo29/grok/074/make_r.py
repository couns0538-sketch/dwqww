#!/usr/bin/env python3
"""Random legal games with SEED. Keep a position every 7 plies after ply 8.

A game that ends under the rules (including threefold and the 50-move rule)
is dropped. Games are cut at ply 64 if they have not ended.
"""

import random
from pathlib import Path

import chess

SEED = 7401
HORIZON = 64
WANT = 400
OUT = Path(__file__).resolve().parent / "R.fens"


def main():
    rng = random.Random(SEED)
    kept = []
    started = 0
    dropped = 0
    while len(kept) < WANT:
        started += 1
        board = chess.Board()
        sample = []
        ended = False
        for ply in range(1, HORIZON + 1):
            if board.is_game_over(claim_draw=True):
                ended = True
                break
            move = rng.choice(list(board.legal_moves))
            board.push(move)
            if ply > 8 and (ply - 8) % 7 == 0:
                sample.append(board.fen())
            if board.is_game_over(claim_draw=True):
                ended = True
                break
        if ended or len(sample) == 0:
            dropped += 1
            continue
        kept.extend(sample)
    kept = kept[:WANT]
    OUT.write_text("\n".join(kept) + "\n", encoding="utf-8")
    print(f"games_started {started} dropped {dropped} positions {len(kept)} seed {SEED}")


if __name__ == "__main__":
    main()
