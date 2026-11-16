#!/usr/bin/env python3
"""py_perft2.py -- python-chess's own perft 2 on the S-F2 board, computed with a plain
recursion (python-chess 1.11.2 has no Board.perft), and the same with the status forced VALID."""
import sys
import chess

FEN = "3k4/3P1q2/5K2/8/8/5r2/7p/7R w - - 0 1"


def perft(b, depth):
    if depth == 0:
        return 1
    if depth == 1:
        return b.legal_moves.count()
    n = 0
    for m in list(b.legal_moves):
        b.push(m)
        n += perft(b, depth - 1)
        b.pop()
    return n


def divide(b, depth):
    out = []
    for m in list(b.legal_moves):
        b.push(m)
        out.append((m.uci(), perft(b, depth - 1)))
        b.pop()
    return out


L = []
b = chess.Board(FEN)
L.append("FEN: %s" % FEN)
L.append("status: %d (IMPOSSIBLE_CHECK bit set: %s)"
         % (b.status(), bool(b.status() & chess.STATUS_IMPOSSIBLE_CHECK)))
L.append("legal moves as-is: %d -> %s" % (b.legal_moves.count(),
                                          [m.uci() for m in b.legal_moves]))
L.append("divide 2 (as-is): %s" % divide(b, 2))
L.append("perft 2 (as-is): %d" % perft(b, 2))
c = chess.Board(FEN)
c._status = chess.STATUS_VALID
L.append("with status forced VALID: legal %d, perft 2 %d, divide 2 %s"
         % (c.legal_moves.count(), perft(c, 2), divide(c, 2)))
txt = "\n".join(L)
open(sys.argv[1], "w").write(txt + "\n")
print(txt)
