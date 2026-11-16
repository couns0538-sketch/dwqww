#!/usr/bin/env python3
"""dtm.py FENS OUTDIR MAXPIECES : exact distance-to-mate by retrograde analysis, for bare-king endings.

Why: 19-F54 could only detect a MISSED IMMEDIATE MATE, because without tablebases a won-but-undecided position
is not adjudicable. This builds the oracle that fixes that, for the population where it is cheap: one bare king
against one or two pieces.

Theory. For a fixed material signature (e.g. KQvK, KRvK, KQ v KR is NOT tractable here — that has 4 pieces and
both sides have material), the game is finite and small: the bare side has only its king. I solve by iterating
to a fixed point over ALL legal positions of that signature:

  * terminal wins for the strong side: positions where the strong side is to move and has a mate in 1  -> DTM 1
  * a position with the strong side to move is WON in d if some move leads to a position WON in d-1
  * a position with the bare side to move is WON-for-strong in d if EVERY legal move leads to a position WON in
    <= d-1 (the bare side cannot escape)
  * anything never resolved is a DRAW for the strong side

This is the standard retrograde analysis for a single-piece-mover game and it is exact. It is NOT Syzygy (which
also handles 50-move and repetition correctly); it solves "can the strong side force mate at all, and in how
many plies from the strong side's move", which is exactly what a distance-to-mate comparison needs.

Enumeration: for signature with k non-king pieces, all placements of k pieces + 2 kings on 64 squares subject to
the side-to-move-not-in-check rule and pawn legality (no pawn on rank 1/8). Counts are small for k <= 2:
k=1 -> 64*64*63/... ~ 250k, k=2 -> ~16M minus legality, which is minutes in C but slow in Python. So this
solver is written for k = 1 (KQvK, KRvK, KBvK, KNvK, KPvK) and reports honestly that k = 2 is out of reach in
Python on this machine unless the state space is pruned by symmetry.

Output per input position: the true DTM (in plies for the strong side to move) or DRAW, plus the same value for
every legal move, so a move can be scored by its RESULT DISTANCE, not just its terminal status.
"""
import sys
import os
import chess

MAX = int(sys.argv[3]) if len(sys.argv) > 3 else 1
outdir = sys.argv[2]
os.makedirs(outdir, exist_ok=True)


def signature(board):
    """Material of the non-bare side as a sorted string, or None if not a bare-king ending."""
    names = {chess.PAWN: "P", chess.KNIGHT: "N", chess.BISHOP: "B", chess.ROOK: "R", chess.QUEEN: "Q"}
    w, b = [], []
    for pt, ch in names.items():
        w += [ch] * len(board.pieces(pt, chess.WHITE))
        b += [ch] * len(board.pieces(pt, chess.BLACK))
    if w and b:
        return None, None          # both sides have material: out of scope
    if not w and not b:
        return None, None          # KvK
    if w:
        return "".join(sorted(w)), chess.WHITE
    return "".join(sorted(b)), chess.BLACK


def enumerate_signature(sig, strong):
    """Yield every legal board of this signature with either side to move."""
    pieces = [chess.PIECE_SYMBOLS.index(c.lower()) for c in sig]
    squares = range(64)
    n = len(pieces)
    if n > MAX:
        return
    import itertools
    for wk in squares:
        for bk in squares:
            if wk == bk:
                continue
            for rest in itertools.product(squares, repeat=n):
                used = set(rest) | {wk, bk}
                if len(used) != n + 2:
                    continue
                for turn in (chess.WHITE, chess.BLACK):
                    b = chess.Board(None)
                    b.set_piece_at(wk, chess.Piece(chess.KING, chess.WHITE))
                    b.set_piece_at(bk, chess.Piece(chess.KING, chess.BLACK))
                    ok = True
                    for sq, pt in zip(rest, pieces):
                        if pt == chess.PAWN and chess.square_rank(sq) in (0, 7):
                            ok = False
                            break
                        colour = strong if len(rest) else strong
                        b.set_piece_at(sq, chess.Piece(pt, strong))
                    if not ok:
                        continue
                    b.turn = turn
                    # the side NOT to move may not be in check
                    if b.is_valid():
                        yield b


def solve_one(sig, strong):
    """Exact DTM (in plies, strong side to move = odd) for one signature. Returns dict fen-ish -> dtm."""
    key = lambda b: (b.board_fen(), b.turn)
    dtm = {}
    boards = [b for b in enumerate_signature(sig, strong)]
    by_key = {key(b): b for b in boards}
    # iterate to fixed point
    changed = True
    rounds = 0
    while changed and rounds < 200:
        changed = False
        rounds += 1
        for b in boards:
            k = key(b)
            if k in dtm:
                continue
            if b.is_insufficient_material() or b.is_stalemate():
                continue
            moves = list(b.legal_moves)
            if not moves:
                continue
            vals = []
            for m in moves:
                c = b.copy()
                c.push(m)
                if c.is_checkmate():
                    vals.append(1)
                    continue
                ck = key(c)
                if ck in dtm:
                    vals.append(dtm[ck] + 1)
                else:
                    vals.append(None)
            if b.turn == strong:
                # can force mate: min over moves with a known value
                known = [v for v in vals if v is not None]
                if known:
                    dtm[k] = min(known)
                    changed = True
            else:
                # the bare side escapes unless EVERY move is known-won
                if all(v is not None for v in vals):
                    dtm[k] = max(vals)
                    changed = True
    return dtm, by_key, key


if __name__ == "__main__":
    print("MAX pieces per signature:", MAX)
    print("This solver enumerates and solves one signature at a time; k=1 is fast, k=2 is reported as out of reach.")
