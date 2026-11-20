#!/usr/bin/env python3
"""300 positions from random legal games.

SEED = seat * 100 + 1. A game is kept only when it is still going at ply 80.
Games that end before that are dropped. From a kept game, one position is
taken every 7 plies after ply 8: plies 15, 22, 29, 36, 43, 50, 57, 64, 71, 78.
"""
import random
import sys
import chess

SEED = 87 * 100 + 1
NEED = 300
LIMIT = 80
SAMPLE = list(range(15, LIMIT, 7))


def main():
    out = sys.argv[1]
    rng = random.Random(SEED)
    kept = []
    dropped = 0
    played = 0
    while len(kept) < NEED:
        board = chess.Board()
        samples = []
        ended = False
        for ply in range(1, LIMIT + 1):
            if board.is_game_over(claim_draw=True):
                ended = True
                break
            moves = list(board.legal_moves)
            board.push(rng.choice(moves))
            if ply in SAMPLE:
                samples.append(board.fen())
        played += 1
        if ended or board.is_game_over(claim_draw=True):
            dropped += 1
            continue
        kept.extend(samples)
    kept = kept[:NEED]
    with open(out, "w", encoding="utf-8") as handle:
        for fen in kept:
            handle.write(fen + "\n")
    sys.stdout.write(f"seed {SEED}\n")
    sys.stdout.write(f"played {played}\n")
    sys.stdout.write(f"dropped {dropped}\n")
    sys.stdout.write(f"positions {len(kept)}\n")
    sys.stdout.write(f"plies {' '.join(str(p) for p in SAMPLE)}\n")


if __name__ == "__main__":
    main()
