#!/usr/bin/env python3
"""Build the area 3 job 2 special-position set from R and G, 500 positions.

Six classes, each found by FILTERING R and G with python-chess. Each class targets a case where
move generation is easy to get wrong; python-chess's perft is the reference for all of them.

  castling_transit_attacked   : the side to move still has a castling right, but the square the king
                                would pass over (f1/d1 / f8/d8) IS attacked by the enemy, so the
                                castling move must NOT be generated although the right exists.
  ep_pseudo_but_illegal       : a pseudo-legal en-passant capture exists but its capture is illegal
                                (it would expose the king), i.e. has_pseudo_legal_en_passant and not
                                has_legal_en_passant.
  capture_promo_check         : a legal capture that promotes AND gives check.
  double_check                : the side to move is in check from two pieces.
  pinned_captures_pinner      : a legal move by a pinned piece that captures the slider giving the pin.
  castling_rook_attacked      : a castling right exists and the ROOK's destination square (d1/f1) is
                                attacked, while the king's transit square is not (legal castling that
                                is only safe because the rook, not the king, is the target).

Usage: gen_special.py R.fens G.epd OUT.fens OUT.tsv NPER
"""
import sys

import chess

BACK_RANK = {chess.WHITE: chess.BB_RANK_1, chess.BLACK: chess.BB_RANK_8}


def _squares(sq):
    return [sq]


def cls_castling_transit_attacked(b):
    """Castling right present, transit square attacked, castling therefore absent from legal moves."""
    if not b.is_valid() or b.is_check():
        return None
    enemy = not b.turn
    out = []
    rank_ok = (b.turn == chess.WHITE and b.king(chess.WHITE) == chess.E1) or \
              (b.turn == chess.BLACK and b.king(chess.BLACK) == chess.E8)
    if not rank_ok:
        return None
    base = chess.E1 if b.turn == chess.WHITE else chess.E8
    transit_k = chess.F1 if b.turn == chess.WHITE else chess.F8
    transit_q = chess.D1 if b.turn == chess.WHITE else chess.D8
    # the rights as python-chess will validate them
    legal_castles = {m.to_square for m in b.legal_moves if b.is_castling(m)}
    if b.has_kingside_castling_rights(b.turn):
        if b.is_attacked_by(enemy, transit_k) and chess.G1 not in legal_castles and \
                (chess.G1 if b.turn == chess.WHITE else chess.G8) not in legal_castles:
            out.append("kingside_transit_attacked")
    if b.has_queenside_castling_rights(b.turn):
        if b.is_attacked_by(enemy, transit_q) and \
                (chess.C1 if b.turn == chess.WHITE else chess.C8) not in legal_castles:
            out.append("queenside_transit_attacked")
    return out or None


def cls_ep_pseudo_but_illegal(b):
    if not b.is_valid():
        return None
    if b.ep_square is None:
        return None
    if b.has_pseudo_legal_en_passant() and not b.has_legal_en_passant():
        return ["ep_pseudo_illegal"]
    return None


def cls_capture_promo_check(b):
    if not b.is_valid():
        return None
    out = []
    for m in b.legal_moves:
        if m.promotion and b.is_capture(m):
            probe = b.copy(stack=False)
            probe.push(m)
            if probe.is_check():
                out.append(m.uci())
    return out or None


def cls_double_check(b):
    if not b.is_valid() or not b.is_check():
        return None
    mask = b.checkers_mask()
    if bin(mask).count("1") >= 2:
        return ["double_check"]
    return None


def cls_pinned_captures_pinner(b):
    if not b.is_valid():
        return None
    out = []
    for m in b.legal_moves:
        if not b.is_capture(m):
            continue
        if not b.is_pinned(b.turn, m.from_square):
            continue
        victim = b.piece_at(m.to_square)
        if victim and victim.piece_type in (chess.BISHOP, chess.ROOK, chess.QUEEN):
            out.append(m.uci())
    return out or None


def cls_castling_rook_attacked(b):
    """A legal castling move where the rook's destination square is attacked."""
    if not b.is_valid():
        return None
    out = []
    for m in b.legal_moves:
        if not b.is_castling(m):
            continue
        rook_dest = chess.F1 if b.is_kingside_castling(m) else chess.D1
        if b.is_attacked_by(not b.turn, rook_dest):
            out.append(m.uci())
    return out or None


CLASSES = [
    ("castling_transit_attacked", cls_castling_transit_attacked),
    ("ep_pseudo_but_illegal", cls_ep_pseudo_but_illegal),
    ("capture_promo_check", cls_capture_promo_check),
    ("double_check", cls_double_check),
    ("pinned_captures_pinner", cls_pinned_captures_pinner),
    ("castling_rook_attacked", cls_castling_rook_attacked),
]


def main():
    r_file, g_file, out_fens, out_tsv, per = (sys.argv[1], sys.argv[2], sys.argv[3],
                                              sys.argv[4], int(sys.argv[5]))
    fens = []
    for path in (r_file, g_file):
        for line in open(path):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            fen = line.split(";")[0].strip() if ";" in line else line
            parts = fen.split()
            if len(parts) == 4:
                fen += " 0 1"
            if len(parts) == 6:
                fens.append(fen)
    print("candidate pool", len(fens), flush=True)
    picked = {}
    tsv = open(out_tsv, "w")
    tsv.write("# class\tpool_index\tfen\tmoves\n")
    for name, fn in CLASSES:
        n = 0
        for i, fen in enumerate(fens):
            if n >= per:
                break
            try:
                b = chess.Board(fen)
                hit = fn(b)
            except Exception:
                continue
            if hit:
                picked.setdefault(name, []).append(fen)
                tsv.write("%s\t%d\t%s\t%s\n" % (name, i, fen, ",".join(hit)))
                n += 1
        print(name, n, flush=True)
    allf = []
    for name, _ in CLASSES:
        allf.extend(picked.get(name, []))
    with open(out_fens, "w") as f:
        for fen in allf:
            f.write(fen + "\n")
    print("total", len(allf), "->", out_fens)


main()
