#!/usr/bin/env python3
"""Random legal games. SEED = seat * 100 + 1. One FEN every 7 plies after ply 8.

A game that ends before ply 8 is dropped. A terminal position is not written.
"""
import random
import sys

import chess

SEED = 42 * 100 + 1
TARGET = 300


def main() -> None:
    rng = random.Random(SEED)
    fens = []
    games = 0
    dropped = 0
    while len(fens) < TARGET:
        board = chess.Board()
        games += 1
        taken = 0
        while not board.is_game_over(claim_draw=True):
            ply = board.ply()
            if ply >= 8 and (ply - 8) % 7 == 0:
                fens.append(board.fen())
                taken += 1
                if len(fens) >= TARGET:
                    break
            moves = list(board.legal_moves)
            board.push(rng.choice(moves))
        if taken == 0:
            dropped += 1
    out = sys.argv[1]
    with open(out, "w", encoding="utf-8") as handle:
        handle.write("\n".join(fens) + "\n")
    print(f"seed {SEED} games {games} dropped_before_ply8 {dropped} fens {len(fens)} file {out}")


if __name__ == "__main__":
    main()
