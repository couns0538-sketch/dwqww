#!/usr/bin/env python3
"""dtm.py FEN [MAXMOVES] : exact distance-to-mate by negamax with mate semantics.

Value convention, from the side to move's point of view:
   0            draw (stalemate / insufficient material / no mate within the window)
  +k (k>0)      the side to move forces checkmate in k of ITS OWN moves
  -k (k>0)      the side to move is checkmated in k of the OPPONENT's moves
Internally a ply-level score is used:  MATE - ply  (mate delivered at that ply).
A node returns the best score for the side to move; children are negated.
Mate distance in MOVES for the side to move = (MATE - score + 1) // 2.
Iterative deepening on the distance window, with a full TT cleared per window.
"""
import sys
import time

import chess

FEN = sys.argv[1]
MAXK = int(sys.argv[2]) if len(sys.argv) > 2 else 20
MATE = 10 ** 7


class DTM:
    def __init__(self, maxply):
        self.tt = {}
        self.nodes = 0
        self.maxply = maxply
        self.deadline = None

    @staticmethod
    def key(b):
        return (b.board_fen(), b.turn, b.castling_rights, b.ep_square)

    def negamax(self, b, ply):
        self.nodes += 1
        if self.nodes % 100000 == 0 and time.monotonic() > self.deadline:
            raise TimeoutError

        if b.is_checkmate():
            return -(MATE - ply)
        if b.is_stalemate() or b.is_insufficient_material():
            return 0
        if ply >= self.maxply:
            return 0                      # unknown: no mate proven inside the window

        k = self.key(b)
        hit = self.tt.get(k)
        if hit is not None:
            return hit

        best = -MATE * 2
        for mv in b.legal_moves:
            b.push(mv)
            s = -self.negamax(b, ply + 1)
            b.pop()
            if s > best:
                best = s
                # A proven mate is not improved by looking further.
                if best > MATE // 2:
                    break
        self.tt[k] = best
        return best


def main():
    b = chess.Board(FEN)
    print("position:", FEN)
    print("side to move:", "white" if b.turn else "black")
    print("legal moves:", b.legal_moves.count())
    for k in range(1, MAXK + 1):
        d = DTM(2 * k)
        d.deadline = time.monotonic() + 100
        try:
            s = d.negamax(b, 0)
        except TimeoutError:
            print(f"  window {k:>2} moves ({2*k:>2} plies): TIMEOUT after {d.nodes} nodes")
            return
        if s > MATE // 2:
            mk = (MATE - s + 1) // 2
            print(f"  window {k:>2} moves: side to move MATES in {mk} -> EXACT")
            print("RESULT: exact distance-to-mate =", mk, "moves (mate delivered by the side to move)")
            return
        if s < -MATE // 2:
            mk = (MATE + s) // 2
            print(f"  window {k:>2} moves: side to move MATED in {mk} -> EXACT")
            print("RESULT: exact distance-to-mate =", mk, "moves (the side to move is mated)")
            return
        print(f"  window {k:>2} moves ({2*k:>2} plies): no mate proven, nodes {d.nodes}")
    print("RESULT: no forced mate within", MAXK, "moves")


if __name__ == "__main__":
    sys.setrecursionlimit(200000)
    main()
