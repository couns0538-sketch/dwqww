#!/usr/bin/env python3
"""matedist.py -- exact forced-mate distance in PLIES. Independent of the engine.

    mated_in_plies(fen, max_plies) -> P or None
        P = smallest number of PLIES after which the side to move is checkmated
            against best defence (the side to move moves first, so P is even).
        None = no forced mate found within max_plies.

    mates_in_plies(fen, max_plies) -> P or None
        Same, for the side to move delivering the mate.

PLIES, not moves. UCI `score mate -1` at a losing root means "mated 2 plies from
now". An earlier version of this file compared a move count against a ply budget
and labelled mate-in-1 positions as "lost in 2"; `--selftest` pins the convention
against scores the ENGINE itself reports (`mate -1` = 2 plies) and against an
independent alpha-beta written from the definition.

Scoring (classic, mate distance folded in so shorter mates win):
    value(node) = -MATE + ply      if the side to move is checkmated at `ply`
    value        = 0               on stalemate
    negamax with alpha-beta; a mate score of +/-MATE is offset by the ply it is
    found at, so the search prefers the shortest mate and the longest defence.

Usage:
  matedist.py --selftest
  matedist.py --fen "..." | --fen-file F [--max-plies 9]
"""
import argparse
import sys

import chess

MATE = 1_000_000


def search(board, depth, ply, alpha, beta):
    """Negative-max with alpha-beta. Returns score from side-to-move's view."""
    if board.is_checkmate():
        return -MATE + ply
    if not any(board.legal_moves):
        return 0
    if depth <= 0:
        return 0

    best = -MATE * 2
    for mv in board.legal_moves:
        board.push(mv)
        v = -search(board, depth - 1, ply + 1, -beta, -alpha)
        board.pop()
        if v > best:
            best = v
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break
    return best


def evaluate(fen, max_plies):
    b = chess.Board(fen)
    if not b.is_valid():
        raise ValueError("illegal position: %s" % fen)
    return search(b, max_plies, 0, -MATE * 2, MATE * 2)


def mated_in_plies(fen, max_plies=9):
    v = evaluate(fen, max_plies)
    if v <= -MATE + max_plies:
        return MATE + v          # v = -MATE + ply  ->  ply
    return None


def mates_in_plies(fen, max_plies=9):
    v = evaluate(fen, max_plies)
    if v >= MATE - max_plies:
        return MATE - v
    return None


# ---------------------------------------------------------------------------
# Second opinion: no alpha-beta, no early exit, plain recursive minimax.
# Only used on the tiny self-test positions; shares no code with search().
# ---------------------------------------------------------------------------
def plain_minimax(board, depth, ply):
    if board.is_checkmate():
        return -MATE + ply
    if not any(board.legal_moves):
        return 0
    if depth <= 0:
        return 0
    best = -MATE * 2
    for mv in list(board.legal_moves):
        board.push(mv)
        v = -plain_minimax(board, depth - 1, ply + 1)
        board.pop()
        if v > best:
            best = v
    return best


def selftest():
    # Expected values: the ENGINE reports `mate -1` on all of these at depth 14+
    # (see job3/m2_engine.txt), and mate -1 means the loser is mated in 2 plies.
    cases = [
        ("6k1/8/5PPP/8/8/8/8/R6K b - - 99 40", 2, "engine: mate -1 (reported board, H=99)"),
        ("6k1/8/5PPP/8/8/8/8/R6K b - - 98 40", 2, "engine: mate -1 (reported board, H=98)"),
        ("1k6/8/2K5/8/7R/8/5p2/1R6 b - - 98 40", 2, "engine: mate -1"),
        ("8/8/5R2/8/8/8/3R4/4K1k1 b - - 98 40", 2, "engine: mate -1"),
        ("1R6/3K4/5R2/8/8/k7/8/8 b - - 98 40", 2, "engine: mate -1"),
        # and the mirror direction: side to move DELIVERS the mate.
        # UCI `mate N` = I mate in N of MY moves; that is 2N-1 plies, so
        # `mate 1` is 1 ply (my move, then the opponent is already mated).
        ("6k1/8/5PPP/8/8/8/8/R6K w - - 98 41", -1, "engine: mate 1 (white mates in 1 ply)"),
    ]
    ok = True
    for fen, expect_signed, note in cases:
        v = evaluate(fen, 7)
        if expect_signed > 0:      # side to move is mated
            got = MATE + v if v <= -MATE + 7 else None
        else:                      # side to move mates
            got = -(MATE - v) if v >= MATE - 7 else None
        b = chess.Board(fen)
        pv = plain_minimax(b, 5, 0)
        plain_ok = (pv <= -MATE + 5) if expect_signed > 0 else (pv >= MATE - 5)
        good = (got == expect_signed) and plain_ok
        ok = ok and good
        print("%-45s ab=%-4s plain=%-9s expect=%-4s %s (%s)" % (
            fen, got, pv, expect_signed, "OK" if good else "MISMATCH", note))
    print("selftest:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--fen")
    ap.add_argument("--fen-file")
    ap.add_argument("--max-plies", type=int, default=9)
    args = ap.parse_args()
    if args.selftest:
        return selftest()
    fens = []
    if args.fen:
        fens.append(args.fen)
    if args.fen_file:
        fens += [l.strip() for l in open(args.fen_file) if l.strip() and not l.startswith("#")]
    for fen in fens:
        print("%-58s mated_in_plies=%s" % (fen, mated_in_plies(fen, args.max_plies)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
