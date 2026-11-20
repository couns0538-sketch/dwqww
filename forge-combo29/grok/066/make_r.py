#!/usr/bin/env python3
"""Random legal games from python-chess. SEED = seat * 100 + 1.

A game that ends before ply 64 is dropped. From a game that reaches ply 64,
one position is kept at ply 8 and every 7 plies after that, while the game
is still going.
"""
import random
import sys

import chess

SEED = 6601
NEED = int(sys.argv[1])
OUT = sys.argv[2]
MAX_PLY = 64


def main() -> None:
    rng = random.Random(SEED)
    kept: list[str] = []
    started = 0
    dropped = 0
    while len(kept) < NEED:
        board = chess.Board()
        started += 1
        samples: list[str] = []
        ended = False
        for ply in range(MAX_PLY):
            if board.is_game_over(claim_draw=True):
                ended = True
                break
            if ply >= 8 and (ply - 8) % 7 == 0:
                samples.append(board.fen())
            board.push(rng.choice(list(board.legal_moves)))
        if ended or board.is_game_over(claim_draw=True):
            dropped += 1
            continue
        kept.extend(samples)
    kept = kept[:NEED]
    with open(OUT, "w") as handle:
        handle.write(f"# seed {SEED} games_started {started} games_dropped {dropped} positions {len(kept)}\n")
        for fen in kept:
            handle.write(fen + "\n")
    print(f"started {started} dropped {dropped} wrote {len(kept)} {OUT}")


if __name__ == "__main__":
    main()
