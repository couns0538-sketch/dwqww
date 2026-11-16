#!/usr/bin/env python3
"""mated.py FEN K : is the side to move MATED in exactly k of the opponent's moves?

Plain minimax over all legal moves, no pruning, no TT. Written to be obviously correct at small k.

is_mated_in(b, k): the side to move is mated in k opponent moves
  = for EVERY legal move of the side to move, the opponent can force mate in <= k moves
    (and the side to move has at least one legal move; zero legal moves means already mate/stalemate)
can_force(b, k): the side to move can force mate in <= k of its own moves
  = exists a move that delivers mate, or a move such that for all replies can_force(next, k-1)
"""
import sys

import chess


def can_force(b, k):
    """Side to move forces mate in <= k of its own moves."""
    if k <= 0:
        return False
    for mv in b.legal_moves:
        b.push(mv)
        if b.is_checkmate():
            b.pop()
            return True
        if b.is_stalemate():
            b.pop()
            continue
        # every reply must still leave the opponent able to be mated in k-1
        all_ok = True
        for reply in b.legal_moves:
            b.push(reply)
            if b.is_checkmate():        # we walked into mate: bad
                b.pop()
                all_ok = False
                break
            if b.is_stalemate():
                b.pop()
                all_ok = False
                break
            ok = can_force(b, k - 1)
            b.pop()
            if not ok:
                all_ok = False
                break
        b.pop()
        if all_ok:
            return True
    return False


def is_mated_in(b, k):
    """Side to move is mated in <= k opponent moves."""
    if k <= 0:
        return False
    moves = list(b.legal_moves)
    if not moves:
        return False                     # already mate or stalemate, not "mated in k"
    for mv in moves:
        b.push(mv)
        ok = can_force(b, k)
        b.pop()
        if not ok:
            return False                 # this move escapes: not mated in k
    return True


def main():
    fen = sys.argv[1]
    kmax = int(sys.argv[2])
    b = chess.Board(fen)
    print("position:", fen, "| side to move:", "white" if b.turn else "black")
    for k in range(1, kmax + 1):
        m = is_mated_in(b, k)
        print(f"  mated in {k} opponent move(s): {m}")
        if m:
            print("RESULT: the side to move IS mated in", k)
            return
    print("RESULT: the side to move is not mated within", kmax, "moves")


if __name__ == "__main__":
    sys.setrecursionlimit(100000)
    main()
