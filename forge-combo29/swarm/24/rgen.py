#!/usr/bin/env python3
"""Make the R position set for this seat: random legal games by python-chess, one position every 7 plies.

SEED comes from this seat's number (24 -> 2401) plus the offset given on the command line, so a repeat run of
job 1 uses a different set (the brief: "R with SEED + 10").
Writes: r_positions_<seed>.fens  (one FEN per line, no comments), and a .txt record of how it was made.
"""
import argparse
import random

import chess


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--games", type=int, default=60)
    ap.add_argument("--plies", type=int, default=120)
    ap.add_argument("--every", type=int, default=7)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    rng = random.Random(a.seed)
    fens = []
    seen = set()
    for g in range(a.games):
        board = chess.Board()
        for ply in range(a.plies):
            moves = list(board.legal_moves)
            if not moves:
                break
            if ply % a.every == 0 and ply > 0:
                f = board.fen()
                if f not in seen:
                    seen.add(f)
                    fens.append(f)
            board.push(rng.choice(moves))
    with open(a.out, "w") as f:
        for fen in fens:
            f.write(fen + "\n")
    with open(a.out + ".how.txt", "w") as f:
        f.write(f"made by rgen.py, python-chess {chess.__version__}\n")
        f.write(f"seed {a.seed}, games {a.games}, max plies per game {a.plies}, one position every {a.every} plies\n")
        f.write(f"{len(fens)} positions, all distinct, none of them a game-end position (the walk stops at game end)\n")
    print(f"{len(fens)} positions -> {a.out}")


if __name__ == "__main__":
    main()
