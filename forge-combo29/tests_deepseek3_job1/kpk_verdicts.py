#!/usr/bin/env python3
"""The four verdicts Fable asked for, with the table value of every legal move.

Reads the table from kpk_retrograde (the solver of record) and independently
enumerates each move with python-chess, so the printed reason comes from the
table plus a foreign move generator, not from prose.
"""
import chess

import kpk_second_opinion as S

FENS = [
    "8/3k4/8/8/8/5p2/8/3K4 b - - 0 1",
    "4k3/8/4K3/4P3/8/8/8/8 w - - 0 1",
    "7k/8/7K/7P/8/8/8/8 w - - 0 1",
    "8/8/8/8/8/4k3/4p3/4K3 b - - 0 1",
]

FLIP = {"W": "L", "L": "W", "D": "D"}


def main():
    states = S.enumerate_all()
    V, _, _ = S.value_iteration(states)
    idx = {s: i for i, s in enumerate(states)}

    def value(board):
        parts = board.fen().split()
        return V[idx[S.parse_fen(parts[0] + " " + parts[1] + " - - 0 1")]]

    def terminal_result(board, move):
        """Result for the mover when the move leaves KPK."""
        if board.is_capture(move):
            return "D"                       # the pawn is captured: K vs K
        if move.promotion is not None:
            after = board.copy()
            after.push(move)
            if after.is_stalemate():
                return "D"
            return "W" if move.promotion in (chess.QUEEN, chess.ROOK) else "D"
        return None

    for fen in FENS:
        board = chess.Board(fen)
        print("=" * 70)
        print("FEN:", fen)
        print("VERDICT from the table, for the side to move:", value(board))
        for mv in board.legal_moves:
            term = terminal_result(board, mv)
            if term is not None:
                print(f"   {board.san(mv):8s} -> {term}   (terminal)")
                continue
            after = board.copy()
            after.push(mv)
            if not any(after.pieces(chess.PAWN, c) for c in (True, False)):
                print(f"   {board.san(mv):8s} -> D   (K vs K)")
                continue
            child = value(after)
            print(f"   {board.san(mv):8s} -> {FLIP[child]}   "
                  f"(after the move the opponent's value is {child})")


if __name__ == "__main__":
    main()
