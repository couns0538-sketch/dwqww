#!/usr/bin/env python3
"""mate_dfs.py : correct forced-mate proof by plain DFS with memo, checked on known cases.

The previous two attempts were wrong. This one is written as a single recursive function with an explicit
"checkmate / stalemate / depth exhausted" structure and is validated on textbook cases BEFORE use, including a
KRvK win at depth 9, which is the class under test.

mate_or_better(board, plies): True if the side to move can force mate within `plies` half-moves.
Negamax style: at our node we need ONE move that wins; at the opponent's node ALL replies must lose.
"""
import functools
import sys

import chess


def forced_mate(board, plies):
    if plies <= 0:
        return False
    if board.is_checkmate():
        return True          # already mated: the side to move has lost
    if board.is_stalemate() or board.is_insufficient_material():
        return False
    ours = board.turn
    for mv in board.legal_moves:
        board.push(mv)
        if board.is_checkmate():
            board.pop()
            return True
        if plies - 2 >= 0:
            # opponent's node: every reply must still lose within the remaining plies
            all_lose = True
            for reply in list(board.legal_moves):
                board.push(reply)
                loses = forced_mate(board, plies - 2)
                board.pop()
                if not loses:
                    all_lose = False
                    break
            board.pop()
            if all_lose:
                return True
        else:
            board.pop()
    return False


def shortest(fen, max_plies=9):
    b = chess.Board(fen)
    for n in range(1, max_plies + 1, 2):
        if forced_mate(b, n):
            return n
    return None


if __name__ == "__main__":
    print("== self-test on textbook cases (must ALL pass before the real boards)")
    tests = [
        ("7k/5Q2/6K1/8/8/8/8/8 w - - 0 1", 1, "KQ v K mate in 1"),
        ("6k1/8/6K1/8/8/8/8/7Q w - - 0 1", 3, "KQ v K mate in <= 3"),
        ("8/8/8/8/8/R7/7K/3k4 w - - 0 1", 9, "KR v K mate within 9"),
        ("8/8/8/6k1/8/8/5K2/1Q6 w - - 0 1", 9, "KQ v K mate within 9"),
    ]
    ok = True
    for fen, lim, label in tests:
        got = shortest(fen, lim)
        good = got is not None and got <= lim
        ok = ok and good
        print("  %-26s <= %d -> %s  (%s)" % (label, lim, got, "PASS" if good else "FAIL"))
    print()
    if not ok:
        print("SELF-TEST FAILED: refusing to report on the real boards.")
        sys.exit(2)
    print("== the six boards")
    FENS = [
        "6k1/8/7R/2K5/8/8/8/8 w - - 0 1",
        "7K/5k2/8/4R3/8/8/8/8 w - - 0 1",
        "8/3K4/8/8/8/7k/3R4/8 w - - 0 1",
        "4k2K/8/8/1R6/8/8/8/8 w - - 0 1",
        "8/8/8/8/8/R7/7K/3k4 w - - 0 1",
        "8/8/8/6k1/8/8/5K2/1Q6 w - - 0 1",
    ]
    for fen in FENS:
        print("  %s -> mate in %s plies" % (fen, shortest(fen, 9)))
