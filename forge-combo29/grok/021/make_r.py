#!/usr/bin/env python3
"""Random legal games with SEED. Keep one FEN every 7 plies after ply 8.

A game that ends before ply 80 is dropped, including every sample from it.
Games that reach ply 80 without ending contribute plies 15, 22, 29, 36, 43, 50, 57, 64, 71, 78.
"""
import random
import sys

import chess

SEED = 2101
HORIZON = 80
WANT = 300


def main() -> int:
    rng = random.Random(SEED)
    kept: list[str] = []
    attempts = 0
    dropped = 0
    while len(kept) < WANT:
        attempts += 1
        if attempts > 100000:
            raise SystemExit(f"only {len(kept)} positions after {attempts} games")
        board = chess.Board()
        sample: list[str] = []
        ended = False
        for ply in range(1, HORIZON + 1):
            if board.is_game_over(claim_draw=True):
                ended = True
                break
            move = rng.choice(list(board.legal_moves))
            board.push(move)
            if ply > 8 and (ply - 8) % 7 == 0:
                sample.append(board.fen())
        if ended or len(sample) == 0:
            dropped += 1
            continue
        kept.extend(sample)
    kept = kept[:WANT]
    out = sys.argv[1]
    with open(out, "w", encoding="utf-8") as handle:
        handle.write("\n".join(kept) + "\n")
    print(f"wrote {len(kept)} fens attempts {attempts} dropped_games {dropped} seed {SEED}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
