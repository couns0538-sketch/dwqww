"""Find a position where a repetition is UNAVOIDABLE inside the tree.

This is the only way to test in-tree repetition detection without relying on
score heuristics: if every legal line reaches a repetition, the search must
return 0 for the reasons the rule-50/repetition branch gives, and the
instrumented counter must fire at ply > 0.

Criterion, all machine-checked with python-chess:

  1. the side to move has at least one legal move,
  2. every legal move, followed by the opponent's best play, returns to a
     position already in the history within a small number of plies,
  3. the repetition is reached with ply > 0 relative to the root.

Rather than guess, this enumerates sparse positions and keeps the ones whose
legal-move count is tiny (so unavoidability is plausible), then verifies
condition 2 by playing every legal move and checking `is_repetition(2)` on the
resulting tree.
"""

import itertools

import chess

MAX_PIECES = 5


def legal_count(board):
    return board.legal_moves.count()


def forced_repetition(fen, plies=6):
    """True when every line from `fen` hits a threefold within `plies`.

    "Every line" is checked by exhaustive play, which is affordable only for
    positions with very few legal moves; callers filter on that first.
    """
    root = chess.Board(fen)
    reached = {"all": True}

    def walk(board, depth):
        if board.is_repetition(2):
            return True
        if depth == 0:
            return False
        moves = list(board.legal_moves)
        if not moves:
            return False
        # every move must be able to reach a repetition
        return all(walk_after(board, m, depth - 1) for m in moves)

    def walk_after(board, move, depth):
        board.push(move)
        try:
            return walk(board, depth)
        finally:
            board.pop()

    return walk(root, plies)


def enumerate_sparse():
    """Sparse K+Q vs K style positions with very few legal moves."""
    out = []
    pieces = [
        (chess.KING, chess.WHITE), (chess.QUEEN, chess.WHITE),
        (chess.KING, chess.BLACK),
    ]
    squares = chess.SQUARES
    for combo in itertools.permutations(squares, 3):
        board = chess.Board(None)
        board.turn = chess.WHITE
        for sq, (pt, cl) in zip(combo, pieces):
            board.set_piece_at(sq, chess.Piece(pt, cl))
        board.castling_rights = chess.BB_EMPTY
        board.ep_square = None
        board.halfmove_clock = 0
        board.fullmove_number = 1
        if not board.is_valid():
            continue
        n = legal_count(board)
        if 1 <= n <= 2:
            out.append((board.fen(), n))
    return out


if __name__ == "__main__":
    cands = enumerate_sparse()
    print("sparse candidates (1-2 legal moves): %d" % len(cands))
    hits = []
    for fen, n in cands:
        if forced_repetition(fen, plies=6):
            hits.append((fen, n))
            print("FORCED REP: %s (legal moves: %d)" % (fen, n))
            if len(hits) >= 5:
                break
    print()
    print("forced-repetition fixtures: %d" % len(hits))
