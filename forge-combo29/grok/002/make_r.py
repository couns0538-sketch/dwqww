#!/usr/bin/env python3
"""Random legal games from python-chess. Seed is the seat seed.

One position every 7 plies after ply 8 (plies 15, 22, 29, 36, 43, 50).
A game that ends before ply 50 is dropped and contributes no position.
"""
import random
import sys

import chess

SEED = 201
PLIES = (15, 22, 29, 36, 43, 50)
WANTED = 300


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: make_r.py <out.epd> <out.meta>", file=sys.stderr)
        return 2
    rng = random.Random(SEED)
    kept: list[str] = []
    used = 0
    dropped = 0
    attempts = 0
    while len(kept) < WANTED:
        attempts += 1
        if attempts > 200000:
            print("FAIL not enough long games", file=sys.stderr)
            return 1
        board = chess.Board()
        sample: list[str] = []
        ended = False
        for ply in range(1, PLIES[-1] + 1):
            if board.is_game_over(claim_draw=True):
                ended = True
                break
            board.push(rng.choice(list(board.legal_moves)))
            if ply in PLIES:
                sample.append(board.fen())
        if ended or board.is_game_over(claim_draw=True) or len(sample) != len(PLIES):
            dropped += 1
            continue
        kept.extend(sample)
        used += 1
    kept = kept[:WANTED]
    open(sys.argv[1], "w", encoding="utf-8").write("\n".join(kept) + "\n")
    open(sys.argv[2], "w", encoding="utf-8").write(
        f"seed {SEED}\n"
        f"plies {' '.join(str(ply) for ply in PLIES)}\n"
        f"wanted {WANTED}\n"
        f"positions {len(kept)}\n"
        f"games_kept {used}\n"
        f"games_dropped {dropped}\n"
        f"attempts {attempts}\n"
        "rule: a game that ends before ply 50 is dropped\n"
    )
    print(f"positions {len(kept)} games_kept {used} games_dropped {dropped}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
