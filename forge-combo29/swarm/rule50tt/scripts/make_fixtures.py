"""Build and validate mate fixtures programmatically.

Hand-written FENs produced three separate fixture faults in this seat before
this file existed: a missing black king, a rank with too few squares, and a KRK
where the rook already checked the idle king (so the position was illegal and
the engine would have refused it). Placing pieces through python-chess and
asserting `is_valid()` removes that class of error.

python-chess is a *validator*; the mate length comes from the independent cached
solver below, not from the engine.
"""
import functools
import json
import sys

import chess

MAX_PLY = 9


def mate_plies(fen, max_ply=MAX_PLY):
    """Smallest odd ply count in which the side to move forces checkmate, or None."""
    board = chess.Board(fen)

    @functools.lru_cache(maxsize=None)
    def forced(key, ply):
        b = chess.Board(key)
        if b.is_checkmate():
            return 0
        if ply <= 0 or b.is_stalemate() or b.is_insufficient_material():
            return None
        for move in b.legal_moves:
            b.push(move)
            if b.is_checkmate():
                b.pop()
                return 1
            if ply >= 3 and not b.is_game_over():
                survivors = False
                worst = 0
                for reply in b.legal_moves:
                    b.push(reply)
                    if b.is_checkmate():
                        survivors = True
                    else:
                        sub = forced(b.fen(), ply - 2)
                        if sub is None:
                            survivors = True
                        else:
                            worst = max(worst, sub)
                    b.pop()
                    if survivors:
                        break
                if not survivors:
                    b.pop()
                    return 1 + worst
            b.pop()
        return None

    for ply in range(1, max_ply + 1, 2):
        r = forced(board.fen(), ply)
        if r is not None:
            return r
    return None


def build(pieces, hm, fullmove=60):
    """pieces: [(square_name, 'K'|'Q'|'R'|'k'...)]. Returns a FEN or raises."""
    b = chess.Board(None)
    for square, symbol in pieces:
        b.set_piece_at(chess.parse_square(square), chess.Piece.from_symbol(symbol))
    b.turn = chess.WHITE
    b.halfmove_clock = hm
    b.fullmove_number = fullmove
    fen = b.fen()
    if not b.is_valid():
        raise ValueError(f"illegal position: {fen} {pieces}")
    # The side NOT to move must not be in check; is_valid covers it, but check
    # it explicitly so the failure names the actual square.
    if b.is_attacked_by(chess.BLACK, b.king(chess.BLACK)) if b.turn == chess.WHITE else False:
        raise ValueError(f"black king already attacked: {fen}")
    return fen


# Each family is a legal placement. Mate lengths span the range the audit needs;
# the short ones are for the exact-clock experiments and the longer ones for the
# distance test.
FAMILIES = {
    # Q+K vs K, mate in 3-5 plies depending on the square.
    "kqk_m3":  [("a1", "K"), ("c2", "Q"), ("h1", "k")],
    "kqk_m5":  [("b3", "K"), ("c2", "Q"), ("h1", "k")],
    "kqk_box": [("a2", "K"), ("b2", "Q"), ("h8", "k")],
    # R+K vs K, which gives the longest basic mates: the far pair is the one to
    # use for a mate distance that exceeds the remaining clock.
    "krk_far": [("a1", "K"), ("a5", "R"), ("h8", "k")],
    "krk_box": [("a1", "K"), ("b6", "R"), ("h8", "k")],
    "krk_edge": [("c3", "K"), ("h1", "R"), ("a8", "k")],
    # KQ vs K where the queen is close: mate in 1.
    "kqk_m1":  [("a1", "K"), ("c7", "Q"), ("h8", "k")],
}

HALFMOVES = [0, 10, 80, 85, 86, 88, 89, 90, 91, 95, 99]


def main():
    out = []
    for name, pieces in FAMILIES.items():
        for hm in HALFMOVES:
            try:
                fen = build(pieces, hm)
            except ValueError as exc:
                print(f"{name:9} hm={hm:3} ILLEGAL  {exc}", flush=True)
                continue
            m = mate_plies(fen)
            row = {
                "name": name,
                "pieces": pieces,
                "fen": fen,
                "halfmove": hm,
                "valid": True,
                "mate_in_plies": m,
                "legal_moves": chess.Board(fen).legal_moves.count(),
            }
            out.append(row)
            print(f"{name:9} hm={hm:3} m={m}  {fen}", flush=True)
    path = sys.argv[1] if len(sys.argv) > 1 else "/tmp/fixtures.json"
    json.dump(out, open(path, "w"), indent=2)
    print(f"\nwrote {path} ({len(out)} validated fixtures)")


if __name__ == "__main__":
    main()
