#!/usr/bin/env python3
"""Random legal positions for set R.

One random.Random stream starts at SEED (seat * 100 + 1). Each move is
random.choice of the legal moves. A game that ends before ply 64 is dropped.
A game that reaches ply 64 without ending keeps the positions at plies
8, 15, 22, 29, 36, 43, 50 and 57 (every 7 plies after ply 8). The terminal
position is never written. python-chess is_game_over(claim_draw=True) is the
end test: checkmate, stalemate, insufficient material, the 50-move rule, and
threefold repetition.
"""
import random
import sys

import chess

SEED = 49 * 100 + 1
TARGET = 400
CUT = 64


def main():
    rng = random.Random(SEED)
    kept = []
    dropped = 0
    played = 0
    while len(kept) < TARGET:
        board = chess.Board()
        samples = []
        ended = False
        for ply in range(CUT):
            if board.is_game_over(claim_draw=True):
                ended = True
                break
            if ply >= 8 and (ply - 8) % 7 == 0:
                samples.append(board.fen())
            board.push(rng.choice(list(board.legal_moves)))
        played += 1
        if ended or board.is_game_over(claim_draw=True):
            dropped += 1
            continue
        kept.extend(samples)
    kept = kept[:TARGET]
    out = sys.argv[1] if len(sys.argv) > 1 else "R.fens"
    with open(out, "w", encoding="utf-8") as handle:
        for fen in kept:
            handle.write(fen + "\n")
    print(f"SEED {SEED} played {played} dropped {dropped} kept {len(kept)} file {out}")


if __name__ == "__main__":
    main()
