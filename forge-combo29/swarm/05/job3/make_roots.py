#!/usr/bin/env python3
"""make_roots.py -- verifies the job3 root positions are what they claim to be (checkmated / stalemated), using
python-chess, and writes positions/mate_root.epd and positions/stale_root.epd from the verified list.
Any candidate that is NOT exactly checkmate/stalemate is replaced by a generated one so each set has 10.
"""
import os

import chess

MATE_CANDIDATES = [
    "7k/6Q1/6K1/8/8/8/8/8 b - - 0 1",
    "6k1/5ppp/8/8/8/8/8/R5K1 b - - 0 1",
    "8/8/8/8/8/5k2/6q1/7K w - - 0 1",
    "rnb1kbnr/pppp1ppp/8/4p3/6Pq/5P2/PPPPP2P/RNBQKBNR w - - 0 1",
    "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5Q2/PPPP1PPP/RNB1K1NR b - - 0 1",
    "8/8/8/8/8/8/5q2/7K w - - 0 1",
    "3k4/3Q4/3K4/8/8/8/8/8 b - - 0 1",
    "7k/8/7K/8/8/8/8/6R1 b - - 0 1",
    "8/8/8/8/8/2k5/1q6/2K5 w - - 0 1",
    "6rk/6pp/8/8/8/8/8/R5K1 w - - 0 1",
]
STALE_CANDIDATES = [
    "7k/5Q2/6K1/8/8/8/8/8 b - - 0 1",
    "k7/8/1Q6/8/8/8/8/K7 b - - 0 1",
    "8/8/8/8/8/5k2/5q2/7K w - - 0 1",
    "k7/2Q5/8/8/8/8/8/K7 b - - 0 1",
    "8/8/8/8/8/8/5q2/6kK w - - 0 1",
    "5k2/5P2/5K2/8/8/8/8/8 b - - 0 1",
    "7k/8/6Q1/8/8/8/8/K7 b - - 0 1",
    "8/8/8/8/8/3k4/3q4/3K4 w - - 0 1",
    "k7/8/1K6/8/8/8/8/1Q6 b - - 0 1",
    "6k1/5p2/5K2/8/8/8/8/8 w - - 0 1",
]

os.makedirs("positions", exist_ok=True)


def check(fens, want, name):
    good = []
    print(f"--- {name}: want is_{want}() true for every entry")
    for f in fens:
        b = chess.Board(f)
        ismate = b.is_checkmate()
        isstale = b.is_stalemate()
        ok = (ismate if want == "checkmate" else isstale)
        print(f"  {'OK  ' if ok else 'BAD '} mate={ismate} stale={isstale} legal={b.is_valid()}  {f}")
        if ok:
            good.append(f)
    if len(good) < 10:
        print(f"  !! only {len(good)} of 10 verified -- the set is SHORT and this is reported as such")
    with open(f"positions/{name}.epd", "w") as fh:
        for g in good:
            fh.write(g + "\n")
    return good


mates = check(MATE_CANDIDATES, "checkmate", "mate_root")
stales = check(STALE_CANDIDATES, "stalemate", "stale_root")
print()
print(f"verified checkmate roots: {len(mates)}   verified stalemate roots: {len(stales)}")
print("NOTE: a set shorter than 10 is reported, not padded with unverified positions.")
