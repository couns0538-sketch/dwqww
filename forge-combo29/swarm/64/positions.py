"""Validate every FEN with python-chess before any cell uses it.

A FEN that the engine silently refuses would search startpos instead, which has a
different node count and a plausible-looking time. python-chess is the independent
check; the engine's own refusal is checked separately in the grid runner.

Rejects a position if it is: illegal, in check with no reply, stalemate, drawn by
insufficient material / 50-move / repetition-at-root (the search then bails without
reading the TT, which is not the cost we are measuring).
"""

from __future__ import annotations

import sys

import chess

# Deliberately varied: opening, French middlegame, IQP, closed, tactical, endgame-ish.
FENS = [
    "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R b KQkq - 4 4",
    "rnbqkb1r/pp3ppp/4pn2/2pp4/2PP4/2N1PN2/PP3PPP/R1BQKB1R w KQkq - 0 6",
    "r1bq1rk1/pp2ppbp/2np1np1/8/2BNP3/2N1BP2/PPPQ2PP/R3K2R w KQ - 5 10",
    "r2q1rk1/pb1nbppp/1p2pn2/2ppN3/3P4/2PBP3/PP1N1PPP/R1BQ1RK1 w - - 2 11",
    "2rq1rk1/1p1bbppp/p1n1pn2/3p4/3P4/P1NBPN2/1PQ2PPP/2RR2K1 w - - 1 15",
    "r4rk1/1pp2ppp/p1nb4/3q4/3P4/2NB1N2/PP3PPP/R2Q1RK1 w - - 3 13",
]


def check(fen: str) -> tuple[bool, str]:
    try:
        b = chess.Board(fen)
    except ValueError as exc:
        return False, f"python-chess rejected: {exc}"
    if not b.is_valid():
        return False, f"python-chess is_valid() False: {b.status()}"
    if b.is_checkmate():
        return False, "checkmate at root"
    if b.is_stalemate():
        return False, "stalemate at root"
    if b.is_insufficient_material():
        return False, "insufficient material at root"
    if b.halfmove_clock >= 100:
        return False, "50-move claim available at root"
    if not b.pseudo_legal_moves or b.legal_moves.count() == 0:
        return False, "no legal moves"
    return True, f"ok legal={b.legal_moves.count()} halfmove={b.halfmove_clock} side={'w' if b.turn else 'b'}"


def main() -> int:
    bad = 0
    print(f"validating {len(FENS)} FENs (denominator literal: {len(FENS)})")
    for i, fen in enumerate(FENS):
        ok, why = check(fen)
        print(f"  [{i}] {'PASS' if ok else 'FAIL'} {why}  :: {fen}")
        if not ok:
            bad += 1
    print(f"\n{len(FENS) - bad}/{len(FENS)} valid")
    if bad:
        print("FAIL: refusing to run a grid containing an invalid position")
        return 1
    print("PASS: all positions valid")
    return 0


if __name__ == "__main__":
    sys.exit(main())
