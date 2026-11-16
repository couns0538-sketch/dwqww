#!/usr/bin/env python3
"""prove_mate.py : correct, small exhaustive mate solver used to verify the claimed mate distances.

The first version of this in check_30F33.py was WRONG: it returned None for textbook KRvK mates in 5. The bug was
that it only looked for a "all opponent replies lose" line but returned before restoring the board on some paths,
and its plies arithmetic mixed up sides. This version is written differently and checked against a KNOWN case
(KQ vs K mate in 1) before it is used on anything.

mate_in(board, n) = the side to move can force checkmate within n PLIES (n odd counts our move last).
"""
import sys

import chess


def mate_in(board, n):
    if n <= 0:
        return False
    if n == 1:
        for mv in board.legal_moves:
            board.push(mv)
            done = board.is_checkmate()
            board.pop()
            if done:
                return True
        return False
    for mv in board.legal_moves:
        board.push(mv)
        if board.is_checkmate():
            board.pop()
            return True
        # opponent to move: they must have NO reply that survives n-2 plies
        survives = False
        for reply in list(board.legal_moves):
            board.push(reply)
            keeps = mate_in(board, n - 2)
            board.pop()
            if not keeps:
                survives = True
                break
        board.pop()
        if survives:
            continue
        # also require the opponent to actually have moves (stalemate is not a mate)
        board.push(mv)
        has_reply = any(True for _ in board.legal_moves)
        board.pop()
        if has_reply:
            return True
    return False


def shortest_mate(fen, max_plies=9):
    b = chess.Board(fen)
    for n in range(1, max_plies + 1, 2):
        if mate_in(b, n):
            return n
    return None


if __name__ == "__main__":
    # --- self-test on KNOWN cases before trusting it on anything ---
    tests = [
        ("7k/5Q2/6K1/8/8/8/8/8 w - - 0 1", 1, "KQ vs K, mate in 1"),
        ("6k1/8/6K1/8/8/8/8/7Q w - - 0 1", 3, "KQ vs K, mate in 3 (ours)"),
    ]
    print("== self-test on known cases")
    ok = True
    for fen, expect, label in tests:
        got = shortest_mate(fen, 9)
        good = got is not None and got <= expect
        ok = ok and good
        print("  %-34s expected <= %d, got %s -> %s" % (label, expect, got, "PASS" if good else "FAIL"))

    print()
    print("== the six boards from seat 30's data, with my corrected solver")
    FENS = [
        "6k1/8/7R/2K5/8/8/8/8 w - - 0 1",
        "7K/5k2/8/4R3/8/8/8/8 w - - 0 1",
        "8/3K4/8/8/8/7k/3R4/8 w - - 0 1",
        "4k2K/8/8/1R6/8/8/8/8 w - - 0 1",
        "8/8/8/8/8/R7/7K/3k4 w - - 0 1",
        "8/8/8/6k1/8/8/5K2/1Q6 w - - 0 1",
    ]
    for fen in FENS:
        print("  %s  -> mate in %s plies" % (fen, shortest_mate(fen, 9)))
    sys.exit(0 if ok else 1)
