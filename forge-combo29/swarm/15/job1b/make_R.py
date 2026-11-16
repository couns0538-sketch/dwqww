#!/usr/bin/env python3
"""make_R.py OUTDIR SEED [N]

Position set R as the brief defines it: random legal games played by python-chess with SEED,
one position taken every 7 plies, written to a file in the folder before it is used.
Skips positions that are already over (checkmate/stalemate) so the set is of playable positions.
"""
import os
import random
import sys

import chess


def main():
    outdir = sys.argv[1]
    seed = int(sys.argv[2])
    n = int(sys.argv[3]) if len(sys.argv) > 3 else 200
    os.makedirs(outdir, exist_ok=True)
    rng = random.Random(seed)
    fens = []
    games = 0
    while len(fens) < n and games < 4000:
        games += 1
        board = chess.Board()
        ply = 0
        while not board.is_game_over(claim_draw=False) and ply < 300 and len(fens) < n:
            moves = list(board.legal_moves)
            if not moves:
                break
            board.push(rng.choice(moves))
            ply += 1
            if ply % 7 == 0 and not board.is_game_over(claim_draw=False):
                f = board.fen()
                if len(board.piece_map()) >= 3:  # skip bare-king leftovers
                    fens.append(f)
    if len(fens) < n:
        raise SystemExit("only %d positions from %d games" % (len(fens), games))
    path = os.path.join(outdir, "R_seed%d.fens" % seed)
    with open(path, "w", encoding="utf-8") as fh:
        for f in fens:
            b = chess.Board(f)
            assert b.is_valid() and not b.is_game_over(claim_draw=False), f
            fh.write(f + "\n")
    mats = {}
    for f in fens:
        b = chess.Board(f)
        k = len(b.piece_map())
        mats[k] = mats.get(k, 0) + 1
    print("%s: %d positions from %d games" % (path, len(fens), games))
    print("piece-count histogram (pieces on board -> positions): %s" % dict(sorted(mats.items())))
    print("positions with <= 8 pieces: %d" % sum(v for k, v in mats.items() if k <= 8))


if __name__ == "__main__":
    main()
