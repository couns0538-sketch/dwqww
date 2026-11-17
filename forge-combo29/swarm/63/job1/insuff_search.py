"""Exhaustive search: does ANY engine-insufficient-material root admit a mating move?

Engine predicate (src/board.cpp:1250): no P/R/Q anywhere; and either <=1 minor total,
or no knights and all bishops on ONE square colour. We enumerate king + same-colour-bishop
configurations and ask python-chess whether any legal move mates.
"""
import itertools
import chess

D = chess.SquareSet(chess.BB_DARK_SQUARES)
L = chess.SquareSet(chess.BB_LIGHT_SQUARES)
DARK = [int(s) for s in D]
LIGHT = [int(s) for s in L]


def engine_insuff(b):
    for pt in (chess.PAWN, chess.ROOK, chess.QUEEN):
        if b.pieces(pt, chess.WHITE) or b.pieces(pt, chess.BLACK):
            return False
    n = b.pieces(chess.KNIGHT, chess.WHITE) | b.pieces(chess.KNIGHT, chess.BLACK)
    bs = b.pieces(chess.BISHOP, chess.WHITE) | b.pieces(chess.BISHOP, chess.BLACK)
    if len(n) + len(bs) <= 1:
        return True
    return len(n) == 0 and (len(bs & D) == 0 or len(bs & L) == 0)


def mate_moves(b):
    out = []
    for m in b.legal_moves:
        b.push(m)
        if b.is_checkmate():
            out.append(m.uci())
        b.pop()
    return out


tested = 0
found = []
# 1 minor total, then 2 and 3 same-colour bishops, then add knights (which break the
# all-bishops-one-colour clause but the <=1-minor clause is separate).
for colour_squares in (DARK, LIGHT):
    sq_pool = colour_squares
    for nwb in (0, 1, 2):
        for nbb in (0, 1, 2):
            if nwb + nbb <= 1 or nwb + nbb > 3:
                continue
            for bk in range(64):
                for wk in range(64):
                    if bk == wk:
                        continue
                    for wbs in itertools.combinations(sq_pool, nwb):
                        if bk in wbs or wk in wbs:
                            continue
                        for bbs in itertools.combinations(sq_pool, nbb):
                            if bk in bbs or wk in bbs:
                                continue
                            if set(wbs) & set(bbs):
                                continue
                            b = chess.Board(None)
                            b.set_piece_at(wk, chess.Piece(chess.KING, chess.WHITE))
                            b.set_piece_at(bk, chess.Piece(chess.KING, chess.BLACK))
                            for s in wbs:
                                b.set_piece_at(s, chess.Piece(chess.BISHOP, chess.WHITE))
                            for s in bbs:
                                b.set_piece_at(s, chess.Piece(chess.BISHOP, chess.BLACK))
                            b.turn = chess.WHITE
                            if not b.is_valid():
                                continue
                            if not engine_insuff(b):
                                continue
                            tested += 1
                            mm = mate_moves(b)
                            if mm:
                                found.append((b.fen(), mm, sorted(wbs), sorted(bbs)))
print("positions_tested_as_engine_insufficient", tested)
print("positions_with_a_mating_move", len(found))
for f in found[:5]:
    print("  MATE_FOUND", f)
