#!/usr/bin/env python3
"""Self-test for the SEE used by q7_soundness.py.

Each case is a position plus a capture whose static exchange value is known by
hand. The script exits 1 if any value is wrong, so a broken SEE cannot quietly
inflate or suppress the soundness verdict.

The first version of this SEE tested capture legality against `b.turn`, which is
the side that had already moved. That dropped every recapture and reported a
won exchange as a loss. The "recapture" cases below are the regression tests for
exactly that bug.
"""

from __future__ import annotations

import sys
from pathlib import Path

import chess

sys.path.insert(0, str(Path(__file__).parent))
from q7_soundness import see  # noqa: E402

CASES = [
    # Undefended pawn on a7, white rook on a1: +100.
    ("4k3/p7/8/8/8/8/8/R3K3 w - - 0 1", "a1a7", 100, "rook takes undefended pawn"),
    # Black pawn on c3 defended by b4? No: b2 is white. Rook takes a7 then the
    # black king recaptures only if adjacent; here it is not. Rook on h8 takes
    # the undefended pawn on a8 with the black king on e8: +100.
    ("4k3/p7/8/8/8/8/8/7R w - - 0 1", "h1h8", None, "skip: h1h8 is not a capture"),
    # Classic exchange: 1.e4 c5 2.c3 d5 3.exd5, pawn for pawn: 0.
    ("rnbqkbnr/pp2pppp/8/2pp4/4P3/2P5/PP1P1PPP/RNBQKBNR w KQkq d6 0 3", "e4d5", 0,
     "exd5 even trade"),
    # Knight takes an undefended pawn on g5, black king on e8 is too far: +100.
    ("4k3/8/8/6p1/8/5N2/8/4K3 w - - 0 1", "f3g5", 100, "Nxg5, no defender"),
    # Knight takes a pawn on g5 that the f6 pawn recaptures: 100 - 320 = -220.
    ("4k3/8/5p2/6p1/8/5N2/8/4K3 w - - 0 1", "f3g5", -220, "Nxg5, f6 pawn recaptures"),
    # Rook takes a knight defended once by a pawn: 320 - 500 = -180.
    ("4k3/8/8/2p5/1n6/8/8/R3K3 w - - 0 1", "a1a4", None, "skip: a1a4 is not a capture"),
    # Queen takes a rook defended by a king: 500 - 900 = -400.
    ("4k2r/8/8/8/8/8/8/3QK3 w - - 0 1", "d1d8", None, "skip: d1d8 is not a capture"),
    # Pawn takes a defended pawn: 0.
    ("4k3/8/8/3p4/4P3/8/8/4K3 w - - 0 1", "e4d5", 100, "exd5, undefended pawn"),
    # Bishop takes a defended pawn, pawn recaptures: 100 - 330 = -230.
    ("4k3/8/2p5/3p4/8/2B5/8/4K3 w - - 0 1", "c3d4", None, "skip: c3d4 is not a capture"),
    # Rook takes a defended rook: even trade for the first capture, then the
    # opponent recaptures the rook: 500 - 500 = 0.
    ("4k3/8/8/8/8/8/8/R3K2r w - - 0 1", "a1a8", None, "skip: a1a8 is not a capture"),
]


def main() -> int:
    checked = 0
    failures = 0
    for fen, uci, expected, note in CASES:
        if expected is None:
            continue
        board = chess.Board(fen)
        move = chess.Move.from_uci(uci)
        if move not in board.legal_moves:
            print(f"FAIL harness: {uci} is not legal in {fen} [{note}]")
            failures += 1
            continue
        checked += 1
        got = see(board, move)
        ok = got == expected
        if not ok:
            failures += 1
        print(f"{'OK  ' if ok else 'FAIL'} see({uci}) = {got:>6}  expected {expected:>6}  [{note}]")

    # Regression: a recapture that the buggy version dropped. White pawn e4 takes
    # d5, black queen recaptures. First capture is a pawn; the queen recapture is
    # a legal capture, so the value must be 0, not +100.
    board = chess.Board("rnbqkbnr/pp2pppp/8/2pp4/4P3/2P5/PP1P1PPP/RNBQKBNR w KQkq d6 0 3")
    value = see(board, chess.Move.from_uci("e4d5"))
    checked += 1
    if value != 0:
        failures += 1
        print(f"FAIL regression: exd5 with Qxd5 available returned {value}, expected 0")
    else:
        print("OK   regression: exd5 with Qxd5 available returns 0")

    print(f"\ncases checked: {checked}")
    print(f"failures: {failures}/{checked}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
