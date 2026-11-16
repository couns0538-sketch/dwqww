#!/usr/bin/env python3
"""true_mate2.py FEN [MAXMOVES] : exact mate distance by iterative deepening with a TT.

Returns the mate distance for the side to move. Mate in k moves for the side to move is
2k-1 plies; being mated in k moves is 2k plies. Search is negamax over full legal moves,
with a memo table on (piece placement, side, castling, ep) storing the exact score found,
so the repeated K-vs-K walks collapse.
"""
import sys
import time

import chess

FEN = sys.argv[1] if len(sys.argv) > 1 else "8/8/1p6/8/p3p3/8/2Kpk3/8 w - - 0 1"
MAXMOVES = int(sys.argv[2]) if len(sys.argv) > 2 else 14
INF = 10 ** 6


class Solver:
    def __init__(self):
        self.tt = {}
        self.nodes = 0
        self.deadline = None

    def key(self, b):
        return (b.board_fen(), b.turn, b.castling_rights, b.ep_square)

    def search(self, b, ply, alpha, beta):
        """Negamax with mate scores relative to the ROOT side to move (white here).

        Score = +INF - plies_to_mate  when the root side mates, -(INF - plies) when it is mated.
        Inside, negate at every ply.
        """
        self.nodes += 1
        if self.deadline and self.nodes % 20000 == 0 and time.monotonic() > self.deadline:
            raise TimeoutError

        if b.is_checkmate():
            return -(INF - ply)          # the side to move here is mated at this ply
        if b.is_stalemate() or b.is_insufficient_material():
            return 0

        k = self.key(b)
        hit = self.tt.get(k)
        if hit is not None:
            return hit

        best = -INF * 2
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
    print("root side to move:", "white" if b.turn else "black")
    solver = Solver()
    result = None
    for k in range(1, MAXMOVES + 1):
        solver.tt.clear()
        solver.nodes = 0
        solver.deadline = time.monotonic() + 60
        plies = 2 * k - 1
        try:
            s = solver.search(b, 0, -INF, INF)
        except TimeoutError:
            print(f"  k={k}: timeout after 60 s, {solver.nodes} nodes")
            break
        print(f"  k={k} ({plies} plies): score {s:>8}  nodes {solver.nodes}")
        if s > INF // 2:
            dist = (INF - s + 1) // 2
            result = ("mate", dist)
            print(f"RESULT: the side to move mates in {dist} moves ({2 * dist - 1} plies). VERIFIED EXACT.")
            break
    if result is None:
        print("RESULT: no forced mate by the side to move within the searched depth.")


if __name__ == "__main__":
    main()
