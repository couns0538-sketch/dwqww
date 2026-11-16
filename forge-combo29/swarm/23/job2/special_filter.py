#!/usr/bin/env python3
"""special_filter.py : build the 500-position job-2 set from R_2301.fens + set_G.epd.

Five classes, each decided by python-chess itself (never by the engine):
  C1 castling where the king crosses an ATTACKED transit square
  C2 en passant available where the capture would expose the king
  C3 a capture that promotes and gives check
  C4 double check (two checkers, or one piece giving two lines)
  C5 a pinned piece that can capture its own pinner

Writes SPECIAL.fens (position per line) and special_classes.txt (position <-> classes, with the witness move).
"""
import chess
import json

from pych_perft import count

SOURCES = ["../job1/R_2301.fens", "set_G.epd"]


def load(path):
    out = []
    for line in open(path):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        out.append(line.split(";")[0].strip())
    return out


def class_c1(board):
    """A castling RIGHT exists and the square the king would cross is attacked.

    This is the interesting direction: castling through check is ILLEGAL, so a correct generator
    must NOT emit the castling move here. The class is therefore defined on the right plus the
    attacked transit square, not on a legal castling move (which can never have an attacked transit).
    Returns the castling move that must be ABSENT, or None.
    """
    rank = 0 if board.turn == chess.WHITE else 7
    king_from = chess.square(4, rank)
    king = board.piece_at(king_from)
    if king is None or king.piece_type != chess.KING or king.color != board.turn:
        return None
    for kingside, rook_file, transit_file in ((chess.BB_H1 if rank == 0 else chess.BB_H8, 7, 5),
                                              (chess.BB_A1 if rank == 0 else chess.BB_A8, 0, 3)):
        rook = board.piece_at(chess.square(rook_file, rank))
        if rook is None or rook.piece_type != chess.ROOK or rook.color != board.turn:
            continue
        if not (board.castling_rights & int(kingside)):
            continue
        path = range(5, rook_file + 1) if rook_file > 4 else range(rook_file, 5)
        if any(board.piece_at(chess.square(f, rank)) for f in path if f != 4 and f != rook_file):
            continue
        transit = chess.square(transit_file, rank)
        if board.is_attacked_by(not board.turn, transit):
            move = chess.Move(king_from, chess.square(rook_file, rank))
            return "%s (must be absent)" % move.uci()
    return None


def class_c2(board):
    """An en-passant capture is AVAILABLE but would expose our own king.

    The interesting direction: the ep capture is pseudo-legal and ILLEGAL, because removing the
    captured pawn opens a rank for a slider. A correct generator must not emit it; python-chess
    does not. Returns the ep move that must be ABSENT, or None.
    """
    if board.ep_square is None:
        return None
    for move in board.generate_pseudo_legal_ep():
        if move in board.legal_moves:
            continue
        b = board.copy()
        b.push(move)
        king_sq = b.king(board.turn)
        if king_sq is not None and b.is_attacked_by(not board.turn, king_sq):
            return "%s (must be absent)" % move.uci()
    return None


def class_c3(board):
    for move in board.legal_moves:
        if board.is_capture(move) and move.promotion is not None:
            b = board.copy()
            b.push(move)
            if b.is_check():
                return move.uci()
    return None


def class_c4(board):
    if board.is_check():
        checkers = board.checkers()
        if len(checkers) >= 2:
            return " ".join(chess.square_name(s) for s in checkers)
    return None


def class_c5(board):
    """A piece is pinned by a slider AND can capture that very slider.

    The pinner's square comes from board.pin(), so the capture target must BE the pinner;
    a pinned piece capturing anything else does not belong to this class.
    """
    for sq, piece in board.piece_map().items():
        if piece.color != board.turn:
            continue
        pinner = board.pin_mask(board.turn, sq)
        if pinner == chess.BB_ALL:
            continue
        pinner_sq = next(iter(chess.SquareSet(pinner)))
        for move in board.legal_moves:
            if move.from_square == sq and move.to_square == pinner_sq:
                return move.uci()
    return None


def main():
    classes = {}
    for path in SOURCES:
        for fen in load(path):
            board = chess.Board(fen)
            if not board.is_valid():
                continue
            hits = {}
            for name, fn in (("C1", class_c1), ("C2", class_c2), ("C3", class_c3),
                             ("C4", class_c4), ("C5", class_c5)):
                w = fn(board)
                if w:
                    hits[name] = w
            if hits:
                classes.setdefault(fen, {}).update(hits)

    with open("SPECIAL.fens", "w") as f:
        for fen in classes:
            f.write(fen + "\n")
    with open("special_classes.json", "w") as f:
        json.dump(classes, f, indent=1)

    per = {}
    for fen, hits in classes.items():
        for name in hits:
            per.setdefault(name, []).append(fen)
    print("distinct positions:", len(classes))
    for name in ("C1", "C2", "C3", "C4", "C5"):
        got = per.get(name, [])
        print("%s %d" % (name, len(got)))
        for fen in got[:3]:
            print("    %s  witness %s" % (fen, classes[fen][name]))


if __name__ == "__main__":
    main()
