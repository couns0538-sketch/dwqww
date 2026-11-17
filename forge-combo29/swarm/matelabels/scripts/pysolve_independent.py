#!/usr/bin/env python3
"""Independent mate solver on python-chess. Shares no code with the C++ oracle.

Obvious-by-construction: plain negamax over "mate within k plies" with a
transposition table. The TT is a pure memo of the same predicate, so it changes
nothing but speed.

fixes vs the first draft:
  * stalemate is NOT a mate (defender with no legal moves and no check survives)
  * memoised on (position, k)
"""
import chess
import sys

sys.setrecursionlimit(100000)


class Solver:
    def __init__(self):
        self.memo = {}
        self.nodes = 0

    def forces(self, board, k):
        """Can the side to move force checkmate in <= k plies?"""
        if k <= 0:
            return False
        key = (board._transposition_key(), k)
        hit = self.memo.get(key)
        if hit is not None:
            return hit
        self.nodes += 1
        result = False
        for move in board.legal_moves:
            board.push(move)
            if board.is_checkmate():
                board.pop()
                result = True
                break
            legal_replies = board.legal_moves.count()
            if legal_replies == 0:
                # stalemate: not a win
                board.pop()
                continue
            if k >= 2:
                defended = True
                for reply in board.legal_moves:
                    board.push(reply)
                    ok = self.forces(board, k - 2)
                    board.pop()
                    if not ok:
                        defended = False
                        break
                if defended:
                    board.pop()
                    result = True
                    break
            board.pop()
        self.memo[key] = result
        return result

    def exact(self, fen, cap_plies=9):
        """Shortest forced-mate distance in PLIES for the side to move, or None."""
        board = chess.Board(fen)
        if board.is_checkmate():
            return 0
        for k in range(1, cap_plies + 1, 2):
            if self.forces(board, k):
                return k
        return None


def exact_plies(fen, cap_plies=9):
    s = Solver()
    return s.exact(fen, cap_plies), s.nodes


if __name__ == "__main__":
    for fen in sys.argv[1:]:
        d, n = exact_plies(fen)
        print(f"{d}\t{n}\t{fen}")
