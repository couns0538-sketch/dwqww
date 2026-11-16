#!/usr/bin/env python3
"""Canonical class predicates for the job 2 special set, applied to a FEN.

These are the ONLY definitions of the seven classes; both the set builder and the divide check
call these functions, so a class can never be "claimed" by generator prose. Each returns a list of
short strings (the class's characteristic fact, computed now) or None if the FEN is not in the class.

Written after my first set builder got two of these wrong (white-side rook squares used for black,
and a prose `detail` string that a checker tried to parse); this file replaces both.
"""
import chess


def _is_castle_move(b, m):
    """A castling move is any legal move python-chess reports as castling."""
    return b.is_castling(m)


def castle_transit_attacked(b):
    """A castling RIGHT exists but the king's transit square is attacked, so no castling is legal."""
    if not b.is_valid() or b.is_check() or not b.has_castling_rights(b.turn):
        return None
    if b.king(b.turn) != (chess.E1 if b.turn == chess.WHITE else chess.E8):
        return None
    enemy = not b.turn
    kt = chess.F1 if b.turn == chess.WHITE else chess.F8
    qt = chess.D1 if b.turn == chess.WHITE else chess.D8
    facts = []
    for right, transit in ((b.has_kingside_castling_rights(b.turn), kt),
                           (b.has_queenside_castling_rights(b.turn), qt)):
        if right and b.is_attacked_by(enemy, transit):
            facts.append("transit_%s_attacked" % chess.square_name(transit))
    return facts or None


def castle_rook_path_attacked(b):
    """A legal queenside castling move exists while b1/b8 -- a square only the ROOK crosses -- is
    attacked. This is the legitimate edge case: an attacked rook-path square does NOT forbid
    castling (only the king's own path matters), so a generator that wrongly checks the rook's
    whole path would throw this move away."""
    if not b.is_valid():
        return None
    enemy = not b.turn
    facts = []
    for m in b.legal_moves:
        if not _is_castle_move(b, m):
            continue
        kingside = m.to_square in (chess.G1, chess.G8)
        if kingside:
            continue
        path_sq = chess.B1 if b.turn == chess.WHITE else chess.B8
        if b.is_attacked_by(enemy, path_sq):
            facts.append("rook_path_%s_attacked_%s" % (chess.square_name(path_sq), m.uci()))
    return facts or None


def ep_pseudo_but_illegal(b):
    """An en passant capture is pseudo-legal but not legal (it would expose the king)."""
    if not b.is_valid() or b.ep_square is None:
        return None
    pseudo = [m.uci() for m in b.generate_pseudo_legal_ep()]
    illegal = [u for u in pseudo if chess.Move.from_uci(u) not in b.legal_moves]
    return ["ep_illegal_" + u for u in illegal] or None


def ep_legal(b):
    """An en passant capture is legal."""
    if not b.is_valid() or b.ep_square is None:
        return None
    legal = [m.uci() for m in b.legal_moves if b.is_en_passant(m)]
    return ["ep_legal_" + u for u in legal] or None


def capture_promo_check(b):
    """A legal capture that promotes and gives check."""
    if not b.is_valid():
        return None
    facts = []
    for m in b.legal_moves:
        if m.promotion and b.is_capture(m):
            probe = b.copy(stack=False)
            probe.push(m)
            if probe.is_check():
                facts.append("promo_check_" + m.uci())
    return facts or None


def double_check(b):
    if not b.is_valid() or not b.is_check():
        return None
    n = bin(b.checkers_mask()).count("1")
    return ["checkers_%d" % n] if n >= 2 else None


def pinned_captures_pinner(b):
    """A pinned piece makes a legal capture of an enemy slider."""
    if not b.is_valid():
        return None
    facts = []
    for m in b.legal_moves:
        if not b.is_capture(m) or not b.is_pinned(b.turn, m.from_square):
            continue
        v = b.piece_at(m.to_square)
        if v and v.piece_type in (chess.BISHOP, chess.ROOK, chess.QUEEN):
            facts.append("pinned_takes_" + m.uci())
    return facts or None


CLASSES = {
    "castle_transit_attacked": castle_transit_attacked,
    "castle_rook_path_attacked": castle_rook_path_attacked,
    "ep_pseudo_but_illegal": ep_pseudo_but_illegal,
    "ep_legal": ep_legal,
    "capture_promo_check": capture_promo_check,
    "double_check": double_check,
    "pinned_captures_pinner": pinned_captures_pinner,
}

ORDER = ["castle_transit_attacked", "ep_pseudo_but_illegal", "ep_legal",
         "castle_rook_path_attacked", "capture_promo_check", "double_check",
         "pinned_captures_pinner"]
