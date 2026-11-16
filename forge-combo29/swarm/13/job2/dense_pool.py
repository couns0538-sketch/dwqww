#!/usr/bin/env python3
"""Dense pool for area 3 job 2: play many random games with SEED and test EVERY ply
(not one in seven) for the six special classes, so rare cases actually appear.

This is still "positions I make myself" (R), filtered with python-chess exactly as job 2 says;
R_1301.fens samples one ply in seven, this samples all of them, which is why it is a separate file.

Usage: dense_pool.py SEED NGAMES OUT.tsv MAXPER
Writes one line per hit:  class <TAB> game <TAB> ply <TAB> fen <TAB> detail
"""
import random
import sys

import chess

SEED = int(sys.argv[1])
NGAMES = int(sys.argv[2])
OUT = sys.argv[3]
MAXPER = int(sys.argv[4])

rng = random.Random(SEED)
hits = {}
counts = {}


def note(cls, game, ply, b, detail):
    if counts.get(cls, 0) >= MAXPER:
        return
    counts[cls] = counts.get(cls, 0) + 1
    hits.setdefault(cls, []).append((game, ply, b.fen(en_passant="fen"), detail))


def test(b, game, ply):
    if not b.is_valid():
        return
    # double check (cheap)
    if b.is_check() and bin(b.checkers_mask()).count("1") >= 2:
        note("double_check", game, ply, b, "checkers=%d" % bin(b.checkers_mask()).count("1"))
    # en passant that is pseudo-legal but illegal
    if b.ep_square is not None:
        try:
            if b.has_pseudo_legal_en_passant() and not b.has_legal_en_passant():
                note("ep_pseudo_but_illegal", game, ply, b, "ep=%s" % chess.square_name(b.ep_square))
            elif b.has_legal_en_passant():
                note("ep_legal", game, ply, b, "ep=%s" % chess.square_name(b.ep_square))
        except Exception:
            pass
    # castling classes: only when the side to move has any right
    if b.has_castling_rights(b.turn):
        enemy = not b.turn
        base = chess.E1 if b.turn == chess.WHITE else chess.E8
        kt = chess.F1 if b.turn == chess.WHITE else chess.F8
        qt = chess.D1 if b.turn == chess.WHITE else chess.D8
        kdest = chess.G1 if b.turn == chess.WHITE else chess.G8
        qdest = chess.C1 if b.turn == chess.WHITE else chess.C8
        legal_dests = {m.to_square for m in b.legal_moves if b.is_castling(m)}
        if b.has_kingside_castling_rights(b.turn) and kdest not in legal_dests:
            if b.is_attacked_by(enemy, kt):
                note("castling_transit_attacked", game, ply, b, "kingside transit %s attacked"
                     % chess.square_name(kt))
        if b.has_queenside_castling_rights(b.turn) and qdest not in legal_dests:
            if b.is_attacked_by(enemy, qt):
                note("castling_transit_attacked", game, ply, b, "queenside transit %s attacked"
                     % chess.square_name(qt))
        for d in legal_dests:
            rook_dest = chess.F1 if d in (chess.G1, chess.G8) else chess.D1
            if b.is_attacked_by(enemy, rook_dest):
                note("castling_rook_attacked", game, ply, b, "castles to %s, rook square %s attacked"
                     % (chess.square_name(d), chess.square_name(rook_dest)))
    # capture promotions with check, and pinned-captures-pinner
    promo_hit = None
    pin_hit = None
    for m in b.legal_moves:
        if m.promotion and b.is_capture(m):
            probe = b.copy(stack=False)
            probe.push(m)
            if probe.is_check():
                promo_hit = m.uci()
                break
        if pin_hit is None and b.is_capture(m) and b.is_pinned(b.turn, m.from_square):
            v = b.piece_at(m.to_square)
            if v and v.piece_type in (chess.BISHOP, chess.ROOK, chess.QUEEN):
                pin_hit = m.uci()
    if promo_hit:
        note("capture_promo_check", game, ply, b, promo_hit)
    if pin_hit:
        note("pinned_captures_pinner", game, ply, b, pin_hit)


for g in range(NGAMES):
    board = chess.Board()
    ply = 0
    while board.legal_moves and ply < 300:
        test(board, g, ply)
        moves = list(board.legal_moves)
        board.push(rng.choice(moves))
        ply += 1
    if g % 200 == 0:
        print("game", g, {k: v for k, v in sorted(counts.items())}, flush=True)

with open(OUT, "w") as f:
    f.write("# class\tgame\tply\tfen\tdetail\n")
    for cls, rows in hits.items():
        for game, ply, fen, detail in rows:
            f.write("%s\t%d\t%d\t%s\t%s\n" % (cls, game, ply, fen, detail))
print("FINAL", {k: v for k, v in sorted(counts.items())})
