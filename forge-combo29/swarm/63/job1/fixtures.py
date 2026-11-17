"""Adversarial drawn-root fixtures, each CONSTRUCTED BY SEARCH then ASSERTED with python-chess.

Hand-typed FENs failed twice in a row (a board with one mate where two were claimed, and a
board with a mate where stalemate-only was claimed). So each fixture here is found by a
deterministic search over a small space and its defining property is asserted before use.
A mistyped or misunderstood fixture raises instead of quietly testing the wrong board.
"""
import json

import chess

DARK = chess.SquareSet(chess.BB_DARK_SQUARES)
LIGHT = chess.SquareSet(chess.BB_LIGHT_SQUARES)


def mate_moves(b):
    out = []
    for m in b.legal_moves:
        c = b.copy()
        c.push(m)
        if c.is_checkmate():
            out.append(m.uci())
    return out


def stalemate_moves(b):
    out = []
    for m in b.legal_moves:
        c = b.copy()
        c.push(m)
        if c.is_stalemate():
            out.append(m.uci())
    return out


def build_board(wk, bk, extras, turn=chess.WHITE):
    b = chess.Board(None)
    b.set_piece_at(wk, chess.Piece(chess.KING, chess.WHITE))
    b.set_piece_at(bk, chess.Piece(chess.KING, chess.BLACK))
    for sq, pt, col in extras:
        b.set_piece_at(sq, chess.Piece(pt, col))
    b.turn = turn
    return b


def find_two_mates():
    """K+2R vs K: several mates; take the first legal one with exactly two."""
    for wk in range(64):
        for bk in range(64):
            if wk == bk:
                continue
            for r1 in range(64):
                for r2 in range(r1 + 1, 64):
                    if len({wk, bk, r1, r2}) != 4:
                        continue
                    b = build_board(wk, bk, [(r1, chess.ROOK, chess.WHITE), (r2, chess.ROOK, chess.WHITE)])
                    if not b.is_valid():
                        continue
                    mm = mate_moves(b)
                    if len(mm) == 2:
                        return b, mm
    raise AssertionError("no two-mate position found")


def find_single_mate():
    """K+R vs K with exactly one mate, for the generator-head test."""
    for wk in range(64):
        for bk in range(64):
            if wk == bk:
                continue
            for r in range(64):
                if len({wk, bk, r}) != 3:
                    continue
                b = build_board(wk, bk, [(r, chess.ROOK, chess.WHITE)])
                if not b.is_valid():
                    continue
                mm = mate_moves(b)
                if len(mm) == 1:
                    return b, mm
    raise AssertionError("no single-mate position found")


def find_stalemate_only():
    """K+Q vs K: >=1 move stalemates the bare king and NO move mates."""
    for wk in range(64):
        for bk in range(64):
            if wk == bk:
                continue
            for q in range(64):
                if len({wk, bk, q}) != 3:
                    continue
                b = build_board(wk, bk, [(q, chess.QUEEN, chess.WHITE)])
                if not b.is_valid():
                    continue
                if mate_moves(b):
                    continue
                st = stalemate_moves(b)
                if st:
                    return b, st
    raise AssertionError("no stalemate-only position found")


def find_check_not_mate():
    """A checking move that leaves the defender a legal reply, and no mate at all."""
    for wk in range(64):
        for bk in range(64):
            if wk == bk:
                continue
            for r in range(64):
                if len({wk, bk, r}) != 3:
                    continue
                b = build_board(wk, bk, [(r, chess.ROOK, chess.WHITE)])
                if not b.is_valid() or mate_moves(b):
                    continue
                checks = []
                for m in b.legal_moves:
                    c = b.copy()
                    c.push(m)
                    if c.is_check() and list(c.legal_moves):
                        checks.append(m.uci())
                if checks:
                    return b, checks
    raise AssertionError("no checking-non-mating position found")


def find_mate_in_2_only():
    """White to move, NO mate in 1, but a forced mate in 2 exists."""
    for wk in range(64):
        for bk in range(64):
            if wk == bk:
                continue
            for r in range(64):
                if len({wk, bk, r}) != 3:
                    continue
                b = build_board(wk, bk, [(r, chess.ROOK, chess.WHITE)])
                if not b.is_valid() or mate_moves(b):
                    continue
                for m in b.legal_moves:
                    c1 = b.copy()
                    c1.push(m)
                    if c1.is_checkmate() or c1.is_stalemate():
                        continue
                    # every black reply must allow a mate
                    replies = list(c1.legal_moves)
                    if not replies:
                        continue
                    ok = True
                    for rp in replies:
                        c2 = c1.copy()
                        c2.push(rp)
                        if not mate_moves(c2):
                            ok = False
                            break
                    if ok:
                        return b, m.uci()
    raise AssertionError("no mate-in-2 position found")


def build():
    fx = {}

    def record(key, b, kind, why, **extra):
        assert b.is_valid(), "%s: ILLEGAL FEN %r" % (key, b.fen())
        rec = {
            "fen": b.fen(), "kind": kind, "why": why,
            "legal_moves": b.legal_moves.count(),
            "halfmove": b.halfmove_clock,
            "insufficient": b.is_insufficient_material(),
        }
        rec.update(extra)
        fx[key] = rec
        return rec

    def at_halfmove(b, n, turn=None):
        parts = b.fen().split()
        parts[4] = str(n)
        if turn:
            parts[1] = turn
        out = chess.Board(" ".join(parts))
        assert out.is_valid(), "refused halfmove variant of %r" % b.fen()
        return out

    # A1/A2: two mates, at halfmove 0 and at halfmove 100.
    b2m, mm2 = find_two_mates()
    record("A1_two_mates_h0", at_halfmove(b2m, 0), "control",
           "two distinct mating moves, halfmove 0 (no adjudication can fire)", mating_moves=mm2)
    record("A2_two_mates_h100", at_halfmove(b2m, 100), "halfmove100",
           "two distinct mating moves at halfmove 100: adjudication MUST be cancelled",
           mating_moves=mm2)

    # B: exactly one mate -> the mating move may be the generator head.
    b1m, mm1 = find_single_mate()
    record("B_single_mate_h100", at_halfmove(b1m, 100), "halfmove100",
           "exactly one mating move at halfmove 100", mating_moves=mm1)

    # C: stalemate-only: the repair's in_check() test must NOT cancel the adjudication.
    bst, stm = find_stalemate_only()
    rec = record("C_stalemate_not_mate_h100", at_halfmove(bst, 100), "halfmove100",
                 "moves exist that STALEMATE the bare king; none mates: adjudication must stand",
                 stalemating_moves=stm)
    rec["mating_moves"] = []
    assert mate_moves(at_halfmove(bst, 100)) == []

    # D: a check that is not mate, so the opponent keeps a legal move.
    bchk, chks = find_check_not_mate()
    rec = record("D_check_not_mate_h100", at_halfmove(bchk, 100), "halfmove100",
                 "checking moves leave the defender a reply; no mate anywhere",
                 checking_non_mate_moves=chks)
    rec["mating_moves"] = []

    # E: halfmove 100 with mate in 2 and NO mate in 1.
    bm2, key_move = find_mate_in_2_only()
    rec = record("E_mate_in_2_h100", at_halfmove(bm2, 100), "halfmove100",
                 "mate in 2 exists, mate in 1 does not: adjudication must stand",
                 first_move_of_a_mate_in_2=key_move)
    rec["mating_moves"] = []

    # F: insufficient material, no mate possible under the engine's predicate.
    for key, fen, why in [
        ("F_insuff_KBvK", "8/8/8/8/8/8/8/kBK5 w - - 0 1", "K+B vs K, engine-insufficient"),
        ("F2_insuff_bishops_one_colour", "8/8/8/8/8/8/2b5/kBK5 w - - 0 1",
         "bishops both on the light complex (b1, c2), engine-insufficient"),
    ]:
        b = chess.Board(fen)
        rec = record(key, b, "insufficient", why, mating_moves=mate_moves(b))
        assert rec["mating_moves"] == [], "%s: found a mate, predicate reading is wrong" % key

    # F3: KNN vs K is NOT insufficient for either implementation, and it HAS a mate.
    b = chess.Board("8/8/8/8/8/4N3/3N4/K1k5 w - - 0 1")
    rec = record("F3_KNNvK_not_insufficient", b, "control",
                 "KNN vs K: both implementations say sufficient; a corner mate exists",
                 mating_moves=mate_moves(b))
    assert rec["mating_moves"], "F3: expected a KNNvK mate"

    # G: threefold repetition reached by a real move list (engine key history holds it).
    moves = ["g1f3", "g8f6", "f3g1", "f6g8", "g1f3", "g8f6", "f3g1", "f6g8"]
    b = chess.Board()
    for mv in moves:
        b.push(chess.Move.from_uci(mv))
    assert b.is_repetition(3), "G: move list does not reach a threefold"
    assert b.is_valid()
    assert mate_moves(b) == [], "G: startpos-derived threefold should have no mate"
    fx["G_threefold_root"] = {
        "fen": b.fen(), "kind": "repetition", "moves": moves,
        "why": "threefold repetition claim, no mate available",
        "legal_moves": b.legal_moves.count(), "halfmove": b.halfmove_clock,
        "insufficient": b.is_insufficient_material(), "mating_moves": [],
    }

    return fx


if __name__ == "__main__":
    print(json.dumps(build(), indent=2))
