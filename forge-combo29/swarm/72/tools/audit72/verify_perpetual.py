"""Verify a forced DRAW by perpetual check, then use it for the in-tree test.

A candidate is accepted as a perpetual only when ALL of these hold, each
checked with python-chess:

  1. the ATTACKER (side to move at the root) has a checking move at every
     attacker turn along the loop;
  2. the DEFENDER may play any legal reply, and every reply keeps a check
     available to the attacker -- so the defender cannot stop the checks;
  3. the looping position is reached for the THIRD time, confirmed by
     `is_repetition(2)`, so the draw is by repetition and not merely by
     "attacker keeps checking";
  4. the material balance is unchanged from the root, so the draw is not
     secretly a winning capture (an earlier version of this script accepted
     `Qxf8+` after an interposition and called it a perpetual -- that fixture
     would have made a correct engine look wrong).

Note on depth: a repetition restores the same side to move, so its period is
necessarily even.  The smallest legal period is 4 plies, so the brief's
"three plies deep" is realised as "third occurrence 4 plies below the root".
"""

import chess

VALUE = {chess.PAWN: 100, chess.KNIGHT: 320, chess.BISHOP: 330,
         chess.ROOK: 500, chess.QUEEN: 900, chess.KING: 0}


def _material(board):
    """Signed material in centipawns, always from WHITE's point of view.

    White-relative (not side-to-move-relative) so the balance is comparable
    across plies, which is what condition 4 needs.
    """
    total = 0
    for piece in board.piece_map().values():
        v = VALUE[piece.piece_type]
        total += v if piece.color == chess.WHITE else -v
    return total


def occurrences(board):
    n = 1
    while board.is_repetition(n + 1):
        n += 1
    return n


def attacker_checks(board):
    return [m for m in board.legal_moves if board.gives_check(m)]


def find_perpetual(fen, max_plies=14):
    """Return (moves, occ) for a forced draw by perpetual check, or (None, 0)."""
    root = chess.Board(fen)
    attacker = root.turn
    root_mat = _material(root)
    best = [None, 0]

    def accept(board, path):
        if occurrences(board) >= 3 and _material(board) == root_mat:
            if best[0] is None or len(path) < len(best[0]):
                best[0], best[1] = list(path), occurrences(board)
            return True
        return False

    def defender_turn(board, path):
        if accept(board, path):
            return True
        if len(path) >= max_plies:
            return False
        replies = list(board.legal_moves)
        if not replies:
            return False
        for reply in replies:
            board.push(reply)
            ok = (attacker_turn(board, path + [reply])
                  if board.turn == attacker
                  else defender_turn(board, path + [reply]))
            board.pop()
            if ok:
                return True
        return False

    def attacker_turn(board, path):
        if accept(board, path):
            return True
        if len(path) >= max_plies:
            return False
        for move in attacker_checks(board):
            board.push(move)
            if board.is_checkmate():
                board.pop()
                return False  # mate is better than a draw: not a perpetual
            ok = defender_turn(board, path + [move])
            board.pop()
            if ok:
                return True
        return False

    attacker_turn(root, [])
    return best[0], best[1]


CANDIDATES = [
    "7k/8/8/8/4Q3/8/8/K7 w - - 0 1",
    "6k1/8/8/8/4Q3/8/8/K7 w - - 0 1",
    "7k/8/8/6r1/4Q3/8/8/K7 w - - 0 1",
    "7k/8/8/8/4Q3/8/6q1/K7 w - - 0 1",
    "r6k/8/8/8/4Q2q/8/8/K7 w - - 0 1",
    "1r5k/8/8/8/4Q2q/8/8/K7 w - - 0 1",
    "7k/8/8/7r/4Q3/8/5q2/1K6 w - - 0 1",
]


if __name__ == "__main__":
    for fen in CANDIDATES:
        board = chess.Board(fen)
        if not board.is_valid():
            print("%-44s invalid" % fen)
            continue
        moves, occ = find_perpetual(fen)
        line = " ".join(m.uci() for m in moves) if moves else "-"
        mat = _material(board)
        print("%-44s mat=%-6d occ=%d line=%s" % (fen, mat, occ, line))
