#!/usr/bin/env python3
"""make_R.py SEED count out.fens — random legal games with python-chess.

One position is taken every 7 plies (from a random legal game, max 200 plies), the games driven by
random.choice on the seed. Writes FENs, one per line. Deterministic for a given SEED.
"""
import random
import sys

import chess


def main() -> int:
    seed = int(sys.argv[1])
    count = int(sys.argv[2])
    out = sys.argv[3]
    rng = random.Random(seed)
    fens = []
    while len(fens) < count:
        board = chess.Board()
        for ply in range(1, 201):
            moves = list(board.legal_moves)
            if not moves or board.is_game_over():
                break
            board.push(rng.choice(moves))
            if ply % 7 == 0 and not board.is_game_over():
                fens.append(board.fen())
                if len(fens) >= count:
                    break
    with open(out, "w") as fh:
        for fen in fens:
            fh.write(fen + "\n")
    print(f"wrote {len(fens)} fens to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
