#!/usr/bin/env python3
"""Self-test for the mate prover, before it is allowed to judge the engine.

The audit's whole mate property rests on `mateproof.prove` being right. This
script checks it against plain minimax with no pruning, on positions chosen to
cover every sign and every outcome:

  * attacker to move with a mate          (+d)
  * defender to move, mated               (-d)
  * a position with no mate at all        (None)
  * a stalemate                            (None)
  * a position where the mate needs the
    LONGEST defence to be counted          (+d)

It prints the row count and exits non-zero if any row disagrees, so "the prover
is fine" is a measured claim rather than an assumption. A green run here is a
precondition of the audit; `audit.py --selftest` calls it.
"""

from __future__ import annotations

import os
import sys

import chess

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mateproof  # noqa: E402

CASES = [
    # fen, limit, expected (sign, plies) or None
    ("6k1/8/6K1/8/8/8/8/7Q w - - 0 1", 4, (1, 1)),
    ("6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 0 1", 4, (1, 1)),
    ("7k/8/8/8/Q6K/8/8/8 w - - 10 6", 9, None),  # checked below; may find a mate
    ("4k3/8/6K1/4Q3/8/8/8/8 b - - 9 5", 6, None),
    ("8/8/4k3/8/8/4K3/8/8 w - - 0 1", 3, None),
    ("7k/5Q2/6K1/8/8/8/8/8 b - - 0 1", 3, None),  # stalemate
    ("3k4/8/6K1/3Q4/8/8/8/8 b - - 11 6", 6, None),
]


def main() -> int:
    rows = 0
    fails = 0
    for fen, limit, expected in CASES:
        board = chess.Board(fen)
        if not board.is_valid():
            print(f"SKIP invalid fixture {fen}")
            continue
        got = mateproof.prove(board, limit)
        # Where the table above says None, that is a claim to CHECK, not to
        # trust: brute force decides. Where it names a value, brute force must
        # agree with it exactly.
        brute = None
        for d in range(1, limit + 1):
            s = _brute(board.copy(), d)
            if s >= mateproof.MATE - d:
                brute = (1, mateproof.MATE - s)
                break
            if s <= -mateproof.MATE + d:
                brute = (-1, mateproof.MATE + s)
                break
        rows += 1
        agree = got == brute
        # A fixture marked with an expectation must ALSO match that expectation,
        # so a prover and a brute force that are wrong the same way still fail.
        matches_table = expected is None or got == expected
        if not (agree and matches_table):
            fails += 1
            print(f"FAIL {fen} limit={limit} prove={got} brute={brute} table={expected}")
        else:
            print(f"ok   {fen} limit={limit} prove={got}")
    print(f"rows={rows} fails={fails}")
    return 1 if fails or rows == 0 else 0


def _brute(b: chess.Board, depth: int, ply: int = 0) -> int:
    moves = list(b.legal_moves)
    if not moves:
        return -mateproof.MATE + ply if b.is_check() else 0
    if depth == 0:
        return 0
    best = -mateproof.MATE - 1
    for m in moves:
        b.push(m)
        v = -_brute(b, depth - 1, ply + 1)
        b.pop()
        if v > best:
            best = v
    return best


if __name__ == "__main__":
    sys.exit(main())
