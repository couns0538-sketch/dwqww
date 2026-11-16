#!/usr/bin/env python3
"""forced.py FEN K : is there a FORCED mate in exactly K moves for the side to move?

Plain minimax over all legal moves, no pruning, no TT, no mate-score trickery:
  can_mate(b, k)  : the side to move can force mate in <= k of its own moves
                    = exists a move such that for ALL replies, can_mate(next, k-1)
Written to be obviously correct at small K, not fast. Used only to audit the engine's claim
and my own faster solver.
"""
import sys

import chess


def can_mate(b, k):
    if k <= 0:
        return False
    for mv in b.legal_moves:
        b.push(mv)
        if b.is_checkmate():
            b.pop()
            return True                      # mate delivered by this move
        if b.is_stalemate():
            b.pop()
            continue                          # stalemate is not a mate
        ok = True
        for reply in b.legal_moves:
            b.push(reply)
            if b.is_checkmate():
                b.pop()
                b.pop()
                ok = False                    # we got mated: this move is no good
                break
            if b.is_stalemate():
                b.pop()
                ok = False
                break
            sub = can_mate(b, k - 1)
            b.pop()
            if not sub:
                ok = False
                break
        b.pop()
        if ok:
            return True
    return False


def main():
    fen = sys.argv[1]
    kmax = int(sys.argv[2])
    b = chess.Board(fen)
    print("position:", fen, "| side to move:", "white" if b.turn else "black")
    for k in range(1, kmax + 1):
        r = can_mate(b, k)
        print(f"  forced mate in {k} move(s) for the side to move: {r}")
        if r:
            print("RESULT: the side to move forces mate in", k)
            return
    print("RESULT: no forced mate for the side to move up to", kmax, "moves")


if __name__ == "__main__":
    sys.setrecursionlimit(100000)
    main()
