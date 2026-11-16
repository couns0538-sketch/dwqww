#!/usr/bin/env python3
"""mate_solve.py : correct forced-mate solver, with the INVERSION fixed.

The bug in my earlier attempts: `forced_mate(board, n)` was called at the OPPONENT's node as if the opponent were
trying to mate, so "the opponent has a mate" was confused with "the opponent survives". Here the two sides are
separate functions and never share a return meaning:

  we_mate(board, n)      True  <=> the side to move can force checkmate within n plies
  they_all_lose(board,n) True  <=> EVERY reply by the side to move still lets the opponent force mate within n

we_mate(ours)   = exists move -> (checkmate now) or they_all_lose(after move, n-1)
they_all_lose(board, n) = for all moves: not (board after move is not mate AND we_mate(after, n-1)... )

Concretely, after a white move and with black to move, black "survives" if some black move leads to a position
where white cannot force mate within n-2. So:
  white_mates(b, n) = any move m: b.is_checkmate after m, OR (black has moves and none of them gives
                      white_mates for n-1... )  -- implemented directly below.
Self-tests on textbook positions are MANDATORY and it refuses to report if any fail.
"""
import sys

import chess


def white_can_force_mate(b, n):
    """side to move can force mate within n plies."""
    if n <= 0:
        return False
    for mv in b.legal_moves:
        b.push(mv)
        if b.is_checkmate():
            b.pop()
            return True
        b.pop()
    # no immediate mate: need a move after which EVERY opponent reply loses
    for mv in b.legal_moves:
        b.push(mv)
        opponent_replies = list(b.legal_moves)
        if not opponent_replies:
            # stalemate or mated: mated handled above, so this is stalemate -> not a mate
            b.pop()
            continue
        every_reply_loses = True
        for reply in opponent_replies:
            b.push(reply)
            # now it is our move again, with two fewer plies
            loses = white_can_force_mate(b, n - 2)
            b.pop()
            if not loses:
                every_reply_loses = False
                break
        b.pop()
        if every_reply_loses:
            return True
    return False


def shortest_mate(fen, max_plies=9):
    b = chess.Board(fen)
    if b.is_checkmate():
        return 0 if b.turn == chess.BLACK else None
    for n in range(1, max_plies + 1, 2):
        if white_can_force_mate(b.copy(), n):
            return n
    return None


if __name__ == "__main__":
    print("== MANDATORY self-test on textbook cases")
    tests = [
        ("7k/5Q2/6K1/8/8/8/8/8 w - - 0 1", 1, "KQ v K mate in 1"),
        ("6k1/8/6K1/8/8/8/8/7Q w - - 0 1", 3, "KQ v K mate within 3"),
        ("8/8/8/8/8/R7/7K/3k4 w - - 0 1", 9, "KR v K mate within 9"),
        ("8/8/8/6k1/8/8/5K2/1Q6 w - - 0 1", 9, "KQ v K mate within 9"),
        ("8/8/8/8/8/8/8/K6k w - - 0 1", None, "K v K is NOT a mate"),
        ("7k/5Q2/6K1/8/8/8/8/8 b - - 0 1", None, "black to move, not mated, no forced mate"),
    ]
    ok = True
    for fen, lim, label in tests:
        got = shortest_mate(fen, 9) if lim is not None else shortest_mate(fen, 9)
        if lim is None:
            good = got is None
        else:
            good = got is not None and got <= lim
        ok = ok and good
        print("  %-34s expect %-5s got %-5s %s" % (label, lim, got, "PASS" if good else "FAIL"))
    if not ok:
        print("\nSELF-TEST FAILED — refusing to report on the real boards.")
        sys.exit(2)
    print("\n== the six boards from seat 30's data")
    FENS = [
        "6k1/8/7R/2K5/8/8/8/8 w - - 0 1",
        "7K/5k2/8/4R3/8/8/8/8 w - - 0 1",
        "8/3K4/8/8/8/7k/3R4/8 w - - 0 1",
        "4k2K/8/8/1R6/8/8/8/8 w - - 0 1",
        "8/8/8/8/8/R7/7K/3k4 w - - 0 1",
        "8/8/8/6k1/8/8/5K2/1Q6 w - - 0 1",
    ]
    for fen in FENS:
        print("  %s -> mate in %s plies" % (fen, shortest_mate(fen, 9)))
