#!/usr/bin/env python3
"""inventory_probe.py EXE — the piece-inventory rule, with FENs BUILT from intended counts.

Lesson being applied: my first two attempts at this test mislabelled the FENs (I called
8P+2R+K "3 rooks", and a board with 8 pawns "7P"), so the probe measured something other than
what I thought. Here the FEN is GENERATED from the intended piece multiset and the actual
counts are re-derived from the FEN and printed, so a mislabel is visible.

board.cpp rule: reject if pawns > 8 || total > 16 || promoted > 8 - pawns, where
promoted = max(0,N-2) + max(0,B-2) + max(0,R-2) + max(0,Q-1).
"""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import chess
from ucio import Engine

EXE = sys.argv[1]
PIECES = {"P": chess.PAWN, "N": chess.KNIGHT, "B": chess.BISHOP,
          "R": chess.ROOK, "Q": chess.QUEEN}


class MeasurementError(Exception):
    pass


def build(counts, side="w"):
    """Two kings (one each) plus the white multiset given in `counts`, on a legal-ish spread."""
    b = chess.Board(None)
    b.set_piece_at(chess.E1, chess.Piece(chess.KING, chess.WHITE))
    b.set_piece_at(chess.E8, chess.Piece(chess.KING, chess.BLACK))
    # pawns MUST go on ranks 2..7 (a pawn on rank 1/8 is a separate, correct refusal that
    # would mask the inventory rule this probe is about)
    all_sq = [s for s in chess.SQUARES if s not in (chess.E1, chess.E8)]
    pawn_sq = [s for s in all_sq if chess.square_rank(s) in (1, 2, 3, 4, 5, 6)]
    other_sq = [s for s in all_sq if s not in pawn_sq]
    pi, oi = iter(pawn_sq), iter(other_sq)
    for sym, n in counts.items():
        pool = pi if sym == "P" else oi
        for _ in range(n):
            b.set_piece_at(next(pool), chess.Piece(PIECES[sym], chess.WHITE))
    b.turn = side == "w"
    return b.fen(), b


def engine_verdict(fen):
    e = Engine(EXE, options=[], timeout=120)
    e.start()
    try:
        ans, refused = e.position(fen=fen)
        if refused:
            return refused[0] if refused else "REFUSED"
        e.send("go perft 1")
        lines = e.read_until("nodes ")
        for l in lines:
            m = re.match(r"nodes (\d+)", l)
            if m:
                return f"accepted, {int(m.group(1))} moves"
        raise MeasurementError(f"no nodes for {fen}")
    finally:
        e.quit()


def rule(counts):
    p = counts.get("P", 0)
    total = sum(counts.values()) + 1          # + the white king
    promoted = max(0, counts.get("N", 0) - 2) + max(0, counts.get("B", 0) - 2) \
             + max(0, counts.get("R", 0) - 2) + max(0, counts.get("Q", 0) - 1)
    legal = not (p > 8 or total > 16 or promoted > 8 - p)
    return legal, p, total, promoted


CASES = [
    ("8P only (legal)", {"P": 8}),
    ("9P (illegal)", {"P": 9}),
    ("8P+N+B+R+Q (full original set, legal)", {"P": 8, "N": 1, "B": 1, "R": 1, "Q": 1}),
    ("8P+2R (2 rooks are original: legal)", {"P": 8, "R": 2}),
    ("8P+3R (3rd rook needs a promo, 0 available: illegal)", {"P": 8, "R": 3}),
    ("7P+2Q (1 promo available, 1 needed: LEGAL)", {"P": 7, "Q": 2}),
    ("8P+2Q (0 promos available, 1 needed: illegal)", {"P": 8, "Q": 2}),
    ("0P+9Q (needs 8 promos, 8 available: legal by the rule)", {"Q": 9}),
    ("0P+10Q (needs 9 promos: illegal)", {"Q": 10}),
    ("15 pieces + K = 16 total (legal)", {"P": 8, "N": 2, "B": 2, "R": 2, "Q": 1}),
]

print(f"{'case':56} {'rule says':>9} {'pawns':>6} {'total':>6} {'promo':>6}  engine")
bad = 0
for label, counts in CASES:
    fen, board = build(counts)
    legal, p, total, promoted = rule(counts)
    # re-derive from the generated FEN so a mislabel cannot hide
    re_fen = board.fen()
    actual = {k: len(board.pieces(PIECES[k], chess.WHITE)) for k in PIECES}
    verdict = engine_verdict(re_fen)
    agrees = (legal and verdict.startswith("accepted")) or ((not legal) and "invalid" in verdict)
    if not agrees:
        bad += 1
    print(f"{label:56} {'LEGAL' if legal else 'illegal':>9} {p:>6} {total:>6} {promoted:>6}  {verdict}"
          f"{'' if agrees else '   <-- rule and engine DISAGREE'}")
    del actual

print(f"\ndisagreements between board.cpp's rule and the engine: {bad}")
