#!/usr/bin/env python3
"""inventory_matrix.py EXE — the "impossible piece inventory" check, probed at its boundaries.

board.cpp rejects when `pawns > 8 || total > 16 || promoted > 8 - pawns`, where
promoted = max(0,extra N)+max(0,extra B)+max(0,extra R)+max(0,extra Q) beyond the initial set.
This script walks the boundary: pawns 8/9, total 16/17, and promotion budgets that are exactly
feasible vs one over. python-chess is the reference where it accepts the board.

A missing `nodes`/refusal for any probe aborts the run with no verdict.
"""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import chess
from ucio import Engine

EXE = sys.argv[1]


class MeasurementError(Exception):
    pass


def probe(fen):
    e = Engine(EXE, options=[], timeout=120)
    e.start()
    try:
        ans, refused = e.position(fen=fen)
        if refused:
            return ("REFUSED", refused[0] if refused else "?")
        e.send("go perft 1")
        lines = e.read_until("nodes ")
        n = None
        for l in lines:
            m = re.match(r"nodes (\d+)", l)
            if m:
                n = int(m.group(1))
        if n is None:
            raise MeasurementError(f"no nodes for {fen}")
        return ("ACCEPTED", n)
    finally:
        e.quit()


def pyc(fen):
    try:
        return chess.Board(fen).legal_moves.count()
    except Exception as e:
        return "py-refuses"


CASES = [
    # (label, fen)
    ("8 white pawns (legal max)", "4k3/pppppppp/8/8/8/8/PPPPPPPP/4K3 w - - 0 1"),
    ("9 white pawns", "4k3/8/8/8/8/PPPPPPPPP/8/4K3 w - - 0 1"),
    ("8 pawns + 1 extra queen (feasible)", "4k3/8/8/8/8/8/PPPPPPPP/3QK3 w - - 0 1"),
    ("8 pawns + queen + rook (infeasible)", "4k3/8/8/8/8/8/PPPPPPPP/2QRK3 w - - 0 1"),
    ("0 pawns + 10 queens (infeasible)", "4k3/8/8/8/8/8/8/QQQQQQQQ w - - 0 1"),
    ("0 pawns + 9 queens (infeasible, >8 promos)", "4k3/8/8/8/8/8/8/QQQQQQQK w - - 0 1"),
    ("16 white pieces (legal max)", "4k3/8/8/8/8/8/PPPPPPPP/RNBQKBNR w - - 0 1"),
    ("17 white pieces", "4k3/8/8/8/8/8/PPPPPPPP/RNBQKBNR w - - 0 1"),  # placeholder, see next
    ("17 white: 8P+1Q+2R+2B+2N+K", "4k3/8/8/8/8/8/PPPPPPPP/RNBQQKBNR w - - 0 1"),
    ("both sides 16", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w - - 0 1"),
    ("black 9 pawns", "4k3/ppppppppp/8/8/8/8/PPPPPPPP/4K3 w - - 0 1"),
]

print(f"{'case':42} {'status':10} {'engine':>8} {'py':>6}")
for label, fen in CASES:
    st, v = probe(fen)
    p = pyc(fen)
    print(f"{label:42} {st:10} {str(v):>8} {str(p):>6}")
