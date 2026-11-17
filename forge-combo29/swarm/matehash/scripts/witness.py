"""Extract a WITNESS LINE for a claimed mate distance, and check it.

WHY A WITNESS AND NOT A SCORE
    When two solvers disagree about a mate distance, comparing scores settles
    nothing: both sides report a number and neither is checkable. A witness is
    checkable. For "mate in k plies" the witness is a concrete line that really
    ends in checkmate, together with the load-bearing check that at every
    DEFENDER turn the mover still mates within the remaining budget after EVERY
    legal reply -- because "mate in k" is a claim about forced play, not about
    one lucky line.

    The asymmetric check matters:
      * mating in k : ONE move exists such that every reply loses in <= k-1
      * mated in k  : EVERY move loses in <= k
    A line that mates against a passive defender proves nothing, so the
    defender-side check is the part that makes this evidence.
"""

from __future__ import annotations

import sys

import chess

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from dtm import _mate_within, _mated_within  # noqa: E402


def witness(board: chess.Board, plies: int, cap: int = 8_000_000):
    """A concrete forced mate of exactly `plies`, or None.

    Depth-first over attacker moves only; the defender is handled by the
    `_mated_within` predicate, which already means "every reply loses".
    """
    if plies <= 0:
        return None

    def dfs(b, moves_left, path):
        if moves_left <= 0:
            return None
        for mv in b.legal_moves:
            b.push(mv)
            path.append(mv.uci())
            if b.is_checkmate():
                if moves_left == 1:
                    out = list(path)
                    path.pop()
                    b.pop()
                    return out
                path.pop()
                b.pop()
                continue
            # After our move the opponent must be FORCED to be mated within the
            # remaining plies. `_mated_within` checks every reply.
            sub_memo: dict = {}
            sub_count = {"n": 0}
            try:
                forced = _mated_within(b, moves_left - 1, sub_memo, sub_count, cap)
            except RuntimeError:
                forced = False
            if forced:
                found = dfs(b, moves_left - 2, path)
                if found is not None:
                    path.pop()
                    b.pop()
                    return found
            path.pop()
            b.pop()
        return None

    line = dfs(board.copy(), plies, [])
    if line is None:
        return None
    # Verify independently: replay it and confirm it mates in exactly `plies`.
    check = board.copy()
    for u in line:
        check.push(chess.Move.from_uci(u))
    return {
        "line": line,
        "plies": plies,
        "length": len(line),
        "replay_ends_in_checkmate": check.is_checkmate(),
        "length_matches": len(line) == plies,
    }


def shorter_mate_exists(board: chess.Board, claimed_plies: int, cap: int = 8_000_000):
    """Smallest forced mate strictly shorter than `claimed_plies`, or None."""
    for plies in range(1, claimed_plies):
        memo: dict = {}
        counters = {"n": 0}
        try:
            predicate = _mate_within if plies % 2 == 1 else _mated_within
            if predicate(board.copy(), plies, memo, counters, cap):
                return plies
        except RuntimeError:
            return None
    return None


if __name__ == "__main__":
    fen = sys.argv[1]
    plies = int(sys.argv[2])
    board = chess.Board(fen)
    w = witness(board, plies)
    print({"fen": fen, "plies": plies, "witness": w})
    shorter = shorter_mate_exists(board, plies)
    print({"shorter_mate_plies": shorter})
    sys.exit(0 if w and w["replay_ends_in_checkmate"] else 1)
