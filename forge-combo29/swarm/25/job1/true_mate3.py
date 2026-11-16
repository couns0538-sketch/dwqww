#!/usr/bin/env python3
"""true_mate3.py FEN [MAXMOVES] : exact mate distance, iterative deepening, TT, depth cap.

Score convention (root side to move):
  +INF - plies  the root side mates at that ply
  -(INF - plies) the root side is mated at that ply
Inside the search the score is negated at every ply, so a child returning "I am mated"
becomes "you mate" at the parent.
"""
import sys
import time

import chess

FEN = sys.argv[1] if len(sys.argv) > 1 else "8/8/1p6/8/p3p3/8/2Kpk3/8 w - - 0 1"
INF = 10 ** 6


class Solver:
    def __init__(self, maxply):
        self.tt = {}
        self.nodes = 0
        self.maxply = maxply
        self.deadline = None

    @staticmethod
    def key(b):
        return (b.board_fen(), b.turn, b.castling_rights, b.ep_square)

    def search(self, b, ply, alpha, beta):
        self.nodes += 1
        if self.nodes % 50000 == 0 and time.monotonic() > self.deadline:
            raise TimeoutError
        if b.is_checkmate():
            return -(INF - ply)
        if b.is_stalemate() or b.is_insufficient_material():
            return 0
        if ply >= self.maxply:
            return 0                      # unknown within the window: treat as non-mate
        k = self.key(b)
        if k in self.tt:
            return self.tt[k]
        best = -2 * INF
        for mv in b.legal_moves:
            b.push(mv)
            s = -self.search(b, ply + 1, -beta, -alpha)
            b.pop()
            if s > best:
                best = s
                if s > alpha:
                    alpha = s
                    if alpha >= beta:
                        break
        self.tt[k] = best
        return best


def main():
    b = chess.Board(FEN)
    print("position:", FEN)
    print("side to move:", "white" if b.turn else "black")
    print("legal moves:", b.legal_moves.count())
    for k in range(1, 16):
        s = Solver(2 * k)
        s.deadline = time.monotonic() + 90
        try:
            score = s.search(b, 0, -2 * INF, 2 * INF)
        except TimeoutError:
            print(f"  window {2 * k:>2} plies: timeout ({s.nodes} nodes)")
            return
        tag = ""
        if score > INF // 2:
            d = (INF - score + 1) // 2
            tag = f"  <- root side MATES in {d} moves ({2*d-1} plies)"
        elif score < -INF // 2:
            d = (INF + score) // 2
            tag = f"  <- root side MATED in {d} moves ({2*d} plies)"
        print(f"  window {2 * k:>2} plies: score {score:>8} nodes {s.nodes:>9}{tag}")
        if abs(score) > INF // 2:
            print("RESULT: exact, proven within the window above.")
            return
    print("RESULT: no forced mate proven inside 30 plies.")


if __name__ == "__main__":
    sys.setrecursionlimit(100000)
    main()
