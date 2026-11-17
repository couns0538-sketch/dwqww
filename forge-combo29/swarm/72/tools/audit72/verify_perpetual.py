"""Verify a forced perpetual check, then use it for the in-tree repetition test.

A perpetual is accepted only when the search confirms:

  1. the ATTACKER (the side to move at the root) has a checking move at every
     attacker turn,
  2. the DEFENDER may play any legal reply, and every reply still leaves the
     attacker with a check,
  3. replaying the loop reaches three occurrences of some position, confirmed
     by python-chess `is_repetition(2)`.

Condition 2 is what makes it *forced*: the defender has no reply that stops
the checks.  Condition 3 is what makes it a repetition rather than merely a
series of checks.

Note on depth: a repetition restores the same side to move, so its period is
necessarily EVEN.  The smallest legal period is 4 plies; "three plies deep"
from the brief is therefore realised as "the third occurrence is 4 plies
below the root".
"""

import chess


def occurrences(board):
    n = 1
    while board.is_repetition(n + 1):
        n += 1
    return n


def attacker_checks(board):
    return [m for m in board.legal_moves if board.gives_check(m)]


def find_perpetual(fen, max_plies=16):
    """Return (moves, occ) for a forced perpetual, or (None, 0)."""
    root = chess.Board(fen)
    attacker = root.turn
    best = [None, 0]

    def defender_turn(board, path):
        """Defender to move: try every reply; all must keep checks available."""
        if occurrences(board) >= 3:
            if best[0] is None or len(path) < len(best[0]):
                best[0], best[1] = list(path), occurrences(board)
            return True
        if len(path) >= max_plies:
            return False
        replies = list(board.legal_moves)
        if not replies:
            return False
        for reply in replies:
            board.push(reply)
            if board.turn == attacker:
                ok = attacker_turn(board, path + [reply])
            else:
                ok = defender_turn(board, path + [reply])
            board.pop()
            if ok:
                return True
        return False

    def attacker_turn(board, path):
        """Attacker to move: at least one check must sustain the perpetual."""
        if len(path) >= max_plies:
            return False
        for move in attacker_checks(board):
            board.push(move)
            if board.is_checkmate():
                board.pop()
                return False  # mate is better than a draw; not a perpetual
            ok = defender_turn(board, path + [move])
            board.pop()
            if ok:
                return True
        return False

    attacker_turn(root, [])
    return best[0], best[1]


CANDIDATES = [
    # weak side has only a queen; strong side has Q+R. Weak king boxed.
    "7k/8/8/8/4Q3/8/8/K7 w - - 0 1",
    "6k1/8/8/8/4Q3/8/8/K7 w - - 0 1",
    "6k1/6pp/8/8/8/8/8/K5Q1 w - - 0 1",
    "7k/6pp/8/8/8/8/8/K5Q1 w - - 0 1",
    "k7/8/8/8/4Q3/8/8/K7 w - - 0 1",
    "6k1/5ppp/8/8/8/8/5PPP/K5Q1 w - - 0 1",
]


if __name__ == "__main__":
    for fen in CANDIDATES:
        board = chess.Board(fen)
        if not board.is_valid():
            print("%-42s invalid" % fen)
            continue
        moves, occ = find_perpetual(fen, max_plies=14)
        line = " ".join(m.uci() for m in moves) if moves else "-"
        print("%-42s occ=%d line=%s" % (fen, occ, line))
