#!/usr/bin/env python3
"""ep_common.py : the one raw en-passant test used by filter_special.py, ep_hunt.py and ep_construct.py.

The rule: for the side to move `us`, an en-passant capture is *raw* possible when our pawn stands beside the
double-pushed enemy pawn and the ep target is the empty square on the enemy pawn's rank+1. `raw` ignores
legality — python-chess already leaves an illegal ep capture out of legal_moves, which is exactly why we test the
capture by hand: we want to know whether it WOULD expose our own king.

NOTE (honesty): the first version of this test in this folder (ep_hunt.py, filter_special.py, before 21:16Z)
computed the captured pawn's square as `ep + 8` for White instead of `ep - 8`, so it never found a single class-B
position — those 0 results are void and were re-run with this file.
"""
import chess


def raw_ep_exposes(board):
    """returns (True, '<from><ep>') when a raw ep capture would leave our king attacked, else (False, None)."""
    ep = board.ep_square
    if ep is None:
        return False, None
    us = board.turn
    them = not us
    # the double-pushed enemy pawn: one rank BEHIND the ep target as seen from the side to move
    cap_sq = ep - 8 if us == chess.WHITE else ep + 8
    for df in (-1, 1):
        f = chess.square_file(cap_sq) + df
        if not (0 <= f <= 7):
            continue
        frm = chess.square(f, chess.square_rank(cap_sq))
        p = board.piece_at(frm)
        if p is None or p.piece_type != chess.PAWN or p.color != us:
            continue
        cap = board.piece_at(cap_sq)
        if cap is None or cap.piece_type != chess.PAWN or cap.color != them:
            continue
        b2 = board.copy(stack=False)
        b2.remove_piece_at(frm)
        b2.remove_piece_at(cap_sq)
        b2.set_piece_at(ep, chess.Piece(chess.PAWN, us))
        ksq = b2.king(us)
        if ksq is not None and b2.is_attacked_by(them, ksq):
            return True, f"{chess.square_name(frm)}{chess.square_name(ep)}"
    return False, None


def self_test():
    """known-answer test of this helper: the textbook illegal-ep position must be found, a legal one must not."""
    illegal = chess.Board(None)
    illegal.set_piece_at(chess.D5, chess.Piece(chess.PAWN, chess.WHITE))
    illegal.set_piece_at(chess.E5, chess.Piece(chess.PAWN, chess.BLACK))
    illegal.ep_square = chess.E6
    illegal.set_piece_at(chess.H5, chess.Piece(chess.KING, chess.WHITE))
    illegal.set_piece_at(chess.A5, chess.Piece(chess.ROOK, chess.BLACK))
    illegal.set_piece_at(chess.E8, chess.Piece(chess.KING, chess.BLACK))
    illegal.turn = chess.WHITE
    legal = chess.Board("rnbqkbnr/ppp1pppp/8/3pP3/8/8/PPPP1PPP/RNBQKBNR w KQkq d6 0 3")
    a = raw_ep_exposes(illegal)
    b = raw_ep_exposes(legal)
    return {"illegal_ep_detected": a, "legal_ep": b,
            "pass": a[0] is True and b[0] is False}


if __name__ == "__main__":
    print(self_test())
