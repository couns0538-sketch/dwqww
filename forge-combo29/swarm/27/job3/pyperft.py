#!/usr/bin/env python3
"""pyperft.py - an independent perft on python-chess's move generation.

python-chess 1.11.2 has NO Board.perft (I checked: [m for m in dir(Board) if 'perft' in m] == []),
so my first job-3 harness compared the engine against None and reported 12 "differences" that were
only a missing attribute. This module implements perft with python-chess's own legal_moves, which is
still an independent generator, and every function here RAISES on anything unexpected instead of
returning a sentinel -- a None or a NaN must never be able to pass as a comparison result.
"""
import chess


def perft(board, depth):
    if depth < 0:
        raise ValueError("perft depth must be >= 0, got %r" % (depth,))
    if depth == 0:
        return 1
    if depth == 1:
        return sum(1 for _ in board.legal_moves)
    total = 0
    for mv in board.legal_moves:
        board.push(mv)
        total += perft(board, depth - 1)
        board.pop()
    return total


def perft_fen(fen, depth):
    """Perft of a FEN. Raises on an unparsable FEN; returns an int, never None."""
    board = chess.Board(fen)          # raises ValueError on a bad FEN
    n = perft(board, depth)
    if not isinstance(n, int) or n < 0:
        raise AssertionError("perft produced a non-integer %r for %r depth %r" % (n, fen, depth))
    return n


if __name__ == "__main__":
    # self-check against the three published startpos values
    for depth, want in ((1, 20), (2, 400), (3, 8902), (4, 197281)):
        got = perft_fen(chess.STARTING_FEN, depth)
        assert got == want, "startpos perft %d = %d, expected %d" % (depth, got, want)
        print("startpos perft %d = %d ok" % (depth, got))
    # a planted wrong expectation must FAIL, proving the assert can fire
    try:
        assert perft_fen(chess.STARTING_FEN, 2) == 401, "planted wrong value"
        print("PLANTED WRONG VALUE DID NOT FAIL - the check is blind")
        raise SystemExit(1)
    except AssertionError:
        print("planted wrong value was caught (assert can fire)")
