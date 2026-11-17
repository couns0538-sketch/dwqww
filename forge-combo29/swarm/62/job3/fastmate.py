#!/usr/bin/env python3
"""fastmate.py -- is there a forced mate within k plies? Cheap and exact.

Why a second oracle: matedist.py's `search()` assigns 0 at the horizon, so to
PROVE no mate exists within d plies it must exhaust the whole tree. That is fine
for a handful of positions (the band tables) and hopeless on a corpus (a 10-ply
run over 30 sparse positions did not finish in 10 minutes).

This file answers only the question the corpus scan needs -- "does the side to
move have a forced mate against them within k plies" -- and answers it with the
standard AND/OR formulation, which returns as soon as it finds ONE defence at an
OR node. That is the difference between proving a mate and proving its absence,
and it is what makes a corpus scan affordable.

Semantics, stated because they are the thing that has bitten twice already:
  mated_within(board, k) is True  iff  for EVERY legal move of the side to move,
  the opponent can force checkmate within k-1 further plies. k is in PLIES.
  The predicate therefore reads "the side to move cannot avoid being mated
  within k plies", which is exactly what the band rule `H > 100 - p` needs (with
  p = k).

`--selftest` checks it against matedist.py on positions whose answer is already
established, plus the two reported clocks, so a mistake here shows up as a
disagreement rather than as a confident wrong corpus number.

Usage:
  fastmate.py --selftest
  fastmate.py --fen "..." --k 2
"""
import argparse
import sys

import chess

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from matedist import mated_in_plies  # noqa: E402


def mates_within(board, plies):
    """Side to move can force mate within `plies` plies (OR over own moves)."""
    if plies <= 0:
        return False
    for mv in board.legal_moves:
        board.push(mv)
        done = board.is_checkmate()
        board.pop()
        if done:
            return True
        if plies >= 2 and mated_within(board_after(board, mv), plies - 1):
            return True
    return False


def board_after(board, mv):
    b = board.copy()
    b.push(mv)
    return b


def every_reply_loses(board, plies):
    """Side to move cannot avoid mate within `plies` plies (AND over own moves)."""
    moves = list(board.legal_moves)
    if not moves:
        return board.is_checkmate()
    if plies <= 0:
        return False
    for mv in moves:
        child = board_after(board, mv)
        if child.is_checkmate():
            continue                       # this move loses at once
        if not mates_within(child, plies - 1):
            return False                   # found a defence
    return True


def mated_within(board, plies):
    """True iff the side to move is mated within `plies` plies against all defence."""
    return every_reply_loses(board, plies)


def selftest():
    """Cross-check against matedist on positions whose distance is established."""
    cases = [
        # (fen, expected mated-in plies per matedist/engine `mate -1`)
        ("6k1/8/5PPP/8/8/8/8/R6K b - - 99 40", 2),
        ("6k1/8/5PPP/8/8/8/8/R6K b - - 98 40", 2),
        ("8/8/8/7Q/8/8/1Q5k/1K6 b - - 98 40", 2),
        ("8/1R6/8/5R2/3K4/8/8/5k2 b - - 98 40", 4),
        ("8/8/4k3/8/8/3K4/8/8 b - - 98 40", None),   # bare kings: no mate
    ]
    ok = True
    for fen, expected in cases:
        b = chess.Board(fen)
        ref = mated_in_plies(fen, 8)
        # the fast predicate must agree with the reference at the reference depth
        got = None
        for k in (1, 2, 3, 4, 5, 6, 7, 8):
            if mated_within(b, k):
                got = k
                break
        agree = (got == ref)
        good = agree and (expected is None or got == expected)
        ok = ok and good
        print("%-46s fast=%-4s matedist=%-4s expect=%-4s %s" % (
            fen, got, ref, expected, "OK" if good else "MISMATCH"))
    print("selftest:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--fen")
    ap.add_argument("--k", type=int, default=2)
    args = ap.parse_args()
    if args.selftest:
        return selftest()
    if args.fen:
        b = chess.Board(args.fen)
        print("%s mated_within(%d) = %s" % (args.fen, args.k, mated_within(b, args.k)))
        return 0
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
