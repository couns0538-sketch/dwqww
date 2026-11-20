#!/usr/bin/env python3
"""Random legal games with python-chess.

SEED = seat * 100 + 1. A game that ends (checkmate, stalemate, insufficient
material, threefold, fifty-move, or the variant claim) before ply 64 is
dropped. A game that is still going at ply 64 is kept, and one FEN is taken
at ply 8 and every 7 plies after that (8, 15, 22, 29, 36, 43, 50, 57).
"""
import random
import sys

import chess

SEED = 28 * 100 + 1
NEED = 400
MAX_PLY = 64


def main():
    rng = random.Random(SEED)
    kept = []
    games = 0
    dropped = 0
    while len(kept) < NEED:
        board = chess.Board()
        samples = []
        ended = False
        for ply in range(1, MAX_PLY + 1):
            if board.is_game_over(claim_draw=True):
                ended = True
                break
            move = rng.choice(list(board.legal_moves))
            board.push(move)
            if ply >= 8 and (ply - 8) % 7 == 0:
                samples.append(board.fen())
        games += 1
        if ended or len(samples) == 0:
            dropped += 1
            continue
        kept.extend(samples)
    kept = kept[:NEED]
    out = sys.argv[1]
    with open(out, "w", encoding="utf-8") as handle:
        for fen in kept:
            handle.write(fen + "\n")
    print(f"seed {SEED} games_started {games} dropped {dropped} fens {len(kept)} wrote {out}")


if __name__ == "__main__":
    main()
