"""Bounded proof that the engine's insufficient-material predicate admits NO mating move.

Engine predicate (src/board.cpp:1250-1260): no P/R/Q anywhere, and either
  (a) minor_count <= 1, or
  (b) knights == 0 and all bishops on one square colour.
Case (a): one side has at most one minor and the other none. Enumerated EXHAUSTIVELY
over king+king+one-minor (both colours of minor, both sides) = the whole case.
Case (b): all bishops (both sides) on one colour. Enumerated exhaustively for 1..3
bishops on the chosen colour, both kings anywhere legal.
"""
import itertools
import chess

D = list(chess.SquareSet(chess.BB_DARK_SQUARES))
L = list(chess.SquareSet(chess.BB_LIGHT_SQUARES))


def mate_moves(b):
    out = []
    for m in b.legal_moves:
        b.push(m)
        if b.is_checkmate():
            out.append(m.uci())
        b.pop()
    return out


def place(wk, bk, wpcs, bpcs, turn=chess.WHITE):
    b = chess.Board(None)
    b.set_piece_at(wk, chess.Piece(chess.KING, chess.WHITE))
    b.set_piece_at(bk, chess.Piece(chess.KING, chess.BLACK))
    for s, p in wpcs:
        b.set_piece_at(s, chess.Piece(p, chess.WHITE))
    for s, p in bpcs:
        b.set_piece_at(s, chess.Piece(p, chess.BLACK))
    b.turn = turn
    return b


tested_a = 0
found_a = []
# Case (a): exactly one minor on the board (either colour, either side), rest kings.
for pt in (chess.BISHOP, chess.KNIGHT):
    for side in (chess.WHITE, chess.BLACK):
        for msq in range(64):
            for wk in range(64):
                for bk in range(64):
                    if len({msq, wk, bk}) != 3:
                        continue
                    wp = [(msq, pt)] if side == chess.WHITE else []
                    bp = [(msq, pt)] if side == chess.BLACK else []
                    b = place(wk, bk, wp, bp)
                    if not b.is_valid() or not b.is_insufficient_material():
                        continue
                    tested_a += 1
                    mm = mate_moves(b)
                    if mm:
                        found_a.append((b.fen(), mm))
print("case_a_positions_tested", tested_a)
print("case_a_positions_with_mate", len(found_a))
for f in found_a[:5]:
    print("  A_MATE", f)

tested_b = 0
found_b = []
# Case (b): 1..3 bishops ALL on one colour, both kings anywhere legal.
for pool in (D, L):
    for nb in (1, 2, 3):
        for bsqs in itertools.combinations(pool, nb):
            for wk in range(64):
                for bk in range(64):
                    if wk in bsqs or bk in bsqs or wk == bk:
                        continue
                    # split bishops: side to move gets at least one (worst case for a mate)
                    for k in range(nb + 1):
                        wp = [(s, chess.BISHOP) for s in bsqs[:k]]
                        bp = [(s, chess.BISHOP) for s in bsqs[k:]]
                        b = place(wk, bk, wp, bp)
                        if not b.is_valid() or not b.is_insufficient_material():
                            continue
                        tested_b += 1
                        mm = mate_moves(b)
                        if mm:
                            found_b.append((b.fen(), mm))
print("case_b_positions_tested", tested_b)
print("case_b_positions_with_mate", len(found_b))
for f in found_b[:5]:
    print("  B_MATE", f)
