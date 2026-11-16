#!/usr/bin/env python3
"""ep_construct.py OUT : build class-B positions (an en-passant capture that would expose our own king).

Why constructed and not filtered: filtering R (45,000 random positions) and G (353) with python-chess gave 0
available class-B positions, and 6,000 random games with ep_hunt.py gave 0 too. The pattern needs a slider behind
the capturing pawn on the very rank the double push just landed on, which random play almost never leaves there.

Template (white to move): white pawn d5, black pawn e5 (black just played ...e7-e5), ep square e6, white king h5,
black rook a5, black king e8. dxe6 clears both d5 and e5 and the rook on a5 then attacks h5 → dxe6 is illegal and
the engine must not generate it. Variants: file pair, the row (5th rank only for white-to-move ep), slider type,
king and rook end, black king square, and a few inert pieces.

Every candidate is verified with python-chess: valid, ep square set, the raw ep capture leaves our king attacked,
and the capture is absent from python-chess's legal move list."""
import sys
import chess
from ep_common import raw_ep_exposes

OUT = sys.argv[1]


def build(pf_w, pf_b, slider, king_file, slide_file, black_king, extra):
    """white pawn (pf_w, rank 4), black pawn (pf_b, rank 4) [black just double-pushed], ep = (pf_b, rank 5),
    white king (king_file, rank 4), black slider (slide_file, rank 4), black king at black_king."""
    rank = 4  # 5th rank, index 4
    b = chess.Board(None)
    b.set_piece_at(chess.square(pf_w, rank), chess.Piece(chess.PAWN, chess.WHITE))
    b.set_piece_at(chess.square(pf_b, rank), chess.Piece(chess.PAWN, chess.BLACK))
    b.ep_square = chess.square(pf_b, rank + 1)
    b.set_piece_at(chess.square(king_file, rank), chess.Piece(chess.KING, chess.WHITE))
    b.set_piece_at(chess.square(slide_file, rank), chess.Piece(slider, chess.BLACK))
    b.set_piece_at(chess.parse_square(black_king), chess.Piece(chess.KING, chess.BLACK))
    for sq, piece in extra:
        b.set_piece_at(chess.parse_square(sq), piece)
    b.turn = chess.WHITE
    # fen() would drop an ep square that no legal capture reaches; 'fen' mode keeps it (and that is exactly the
    # class-B situation we want to test)
    return b, f"{chess.square_name(chess.square(pf_w, rank))}{chess.square_name(b.ep_square)}"


cands = []
FILES = ("a", "b", "c", "d", "e", "f", "g", "h")
for pf_w, pf_b in ((3, 4), (4, 3), (1, 2), (2, 1), (5, 6), (6, 5), (2, 3), (5, 4)):
    for slider in (chess.ROOK, chess.QUEEN):
        for black_king in ("e8", "a8", "h8", "b1", "e1"):
            for slide_file, king_file in ((0, 7), (7, 0)):
                b, cap = build(pf_w, pf_b, slider, king_file, slide_file, black_king, [])
                cands.append((b, cap))
                # one variant with an inert pawn far away (makes the position less bare)
                extra = (("a2", chess.Piece(chess.PAWN, chess.WHITE)),
                         ("h7", chess.Piece(chess.PAWN, chess.BLACK)))
                b2, cap2 = build(pf_w, pf_b, slider, king_file, slide_file, black_king, list(extra))
                cands.append((b2, cap2))

seen = {}
for b, cap in cands:
    fen = b.fen(en_passant="fen")
    b2 = chess.Board(fen)
    if fen in seen:
        continue
    if b2.status() != chess.STATUS_VALID:
        seen[fen] = f"invalid status {b2.status()}"
        continue
    ok, cap2 = raw_ep_exposes(b2)
    if not ok:
        seen[fen] = "raw ep does not expose the king"
        continue
    if any(m.to_square == b2.ep_square and b2.is_en_passant(m) for m in b2.legal_moves):
        seen[fen] = "python-chess still allows the ep capture"
        continue
    seen[fen] = "OK"

good = [f for f, v in seen.items() if v == "OK"]
with open(OUT, "w") as f:
    for fen in good:
        f.write(f"B\tCONSTRUCTED\t{fen}\n")
with open(OUT + ".rejects", "w") as f:
    for fen, why in seen.items():
        if why != "OK":
            f.write(f"{why}\t{fen}\n")
print(f"constructed class-B positions: {len(good)} of {len(seen)} distinct candidates")
