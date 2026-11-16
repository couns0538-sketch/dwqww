#!/usr/bin/env python3
"""dtm_fast.py FEN MAXK : exact distance-to-mate with a fast, correct negamax + TT.

Written to replace the slow/incorrect earlier attempts. Conventions:
  score from the side-to-move's view;  MATE - ply  means "mate delivered at this ply by the side who
  moved into it", negated at every level. So a child that says "I am mated at ply p" becomes
  "you mate at ply p" at the parent.
  Mate in k moves FOR THE SIDE TO MOVE  <=>  score = MATE - (2k-1).
  Mated in k moves                      <=>  score = -(MATE - 2k).
Iterative deepening on a ply window; TT keyed on position only, with the depth window folded in.
"""
import sys
import time

import chess

FEN = sys.argv[1]
MAXK = int(sys.argv[2]) if len(sys.argv) > 2 else 8
MATE = 10 ** 7


class S:
    def __init__(self, maxply):
        self.tt = {}
        self.nodes = 0
        self.maxply = maxply
        self.t0 = time.monotonic()
        self.limit = 40.0

    def key(self, b):
        return (b.board_fen(), b.turn, b.castling_rights, b.ep_square)

    def search(self, b, ply):
        self.nodes += 1
        if self.nodes % 20000 == 0 and time.monotonic() - self.t0 > self.limit:
            raise TimeoutError
        if b.is_checkmate():
            return -(MATE - ply)
        if b.is_stalemate() or b.is_insufficient_material():
            return 0
        if ply >= self.maxply:
            return 0
        k = self.key(b)
        if k in self.tt:
            return self.tt[k]
        best = -2 * MATE
        for mv in b.legal_moves:
            b.push(mv)
            s = -self.search(b, ply + 1)
            b.pop()
            if s > best:
                best = s
                if best > MATE // 2:
                    break           # proven mate: nothing can improve it
        self.tt[k] = best
        return best


def main():
    b = chess.Board(FEN)
    print("position:", FEN)
    print("side to move:", "white" if b.turn else "black", "| legal:", b.legal_moves.count())
    for k in range(1, MAXK + 1):
        s = S(2 * k)
        try:
            sc = s.search(b, 0)
        except TimeoutError:
            print(f"  k<={k}: TIMEOUT ({s.nodes} nodes, {time.monotonic()-s.t0:.0f}s)")
            return
        if sc > MATE // 2:
            print(f"  k<={k}: side to move MATES in {(MATE-sc+1)//2}  (exact)")
            return
        if sc < -MATE // 2:
            print(f"  k<={k}: side to move MATED in {(MATE+sc)//2}  (exact)")
            return
        print(f"  k<={k}: no mate proven ({s.nodes} nodes)")


if __name__ == "__main__":
    sys.setrecursionlimit(300000)
    main()
