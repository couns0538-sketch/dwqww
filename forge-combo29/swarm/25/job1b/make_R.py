#!/usr/bin/env python3
"""make_R.py OUT SEED N : the R position set — random legal games, one position every 7 plies.

Random legal games played by python-chess with the given seed; a position is taken every 7 plies, and
only positions that are legal and not terminal are kept. Written to OUT before any use.
"""
import random
import sys

import chess


def main():
    out_path = sys.argv[1]
    seed = int(sys.argv[2])
    want = int(sys.argv[3])
    rng = random.Random(seed)
    fens = []
    guard = 0
    while len(fens) < want and guard < want * 200:
        guard += 1
        b = chess.Board()
        plies = rng.choice([40, 60, 80, 100])
        for ply in range(plies):
            moves = list(b.legal_moves)
            if not moves:
                break
            b.push(rng.choice(moves))
            if (ply + 1) % 7 == 0 and b.is_valid():
                if b.is_checkmate() or b.is_stalemate():
                    continue
                if b.legal_moves.count() == 0:
                    continue
                fens.append(b.fen())
                if len(fens) >= want:
                    break
    seen = set()
    uniq = []
    for f in fens:
        if f in seen:
            continue
        seen.add(f)
        uniq.append(f)
    with open(out_path, "w") as f:
        for fen in uniq[:want]:
            f.write(fen + "\n")
    print(f"wrote {min(len(uniq), want)} positions to {out_path} (seed {seed})")


if __name__ == "__main__":
    main()
