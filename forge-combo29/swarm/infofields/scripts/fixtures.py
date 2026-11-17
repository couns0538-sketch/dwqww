"""Fixture helpers: build FENs with python-chess and validate them.

python-chess is used only as a legality/legality-of-pv oracle, never as an
evaluation oracle. `Board.fen()` is avoided for round-trips (it drops the ep
square); FENs are passed through as literals after validation.
"""

import chess


def validate(fen):
    """Raise unless python-chess accepts the FEN and it round-trips in place."""
    board = chess.Board(fen)
    return board


def mirror_colors(fen):
    """Same board with colours swapped and the side to move swapped."""
    board = chess.Board(fen)
    flipped = board.mirror()
    return flipped.fen(en_passant="fen")


def pv_is_legal(fen, pv):
    """True iff every move in pv is legal in sequence. Returns (ok, detail)."""
    board = chess.Board(fen)
    for i, token in enumerate(pv):
        try:
            move = chess.Move.from_uci(token)
        except ValueError:
            return False, "unparsable move %r at index %d" % (token, i)
        if move not in board.legal_moves:
            return False, "illegal move %r at index %d" % (token, i)
        board.push(move)
    return True, "ok"


def legal_move_count(fen):
    return chess.Board(fen).legal_moves.count()
