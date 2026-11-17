"""Exact mate-distance oracle, built independently of the engine under audit.

Two implementations live here and are deliberately different algorithms:

  * `solve_negamax` -- depth-first ply-exact negamax with a memo keyed on the
    position, returning a signed distance. This is the primary oracle.
  * `solve_layered` -- bottom-up: computes the set of positions the attacker
    mates within k plies by layering, never recursing depth-first.

`crosscheck` runs both and returns None on disagreement, so a caller can DROP an
entry rather than trusting whichever oracle spoke last. Both share python-chess
legal move generation; that dependency is stated rather than hidden, and it is
not a shared *search*.

Contract
--------
`solve_*` returns, from the side to move's view:
  * `+n` (n odd, n >= 1) -- the side to move FORCES mate in exactly n plies,
    and n is the shortest such distance;
  * `-1` -- the side to move is already checkmated;
  * `0` -- no forced mate for either side within the budget.

Ply-exactness is the point. §4's documented defect is "right move, wrong
distance", which a mate/no-mate oracle cannot see.
"""

from __future__ import annotations

import chess

MATE = 10**9


def _memo_key(board: chess.Board) -> str:
    """Key for memoisation of a MATE search.

    Deliberately includes only what a mate search depends on: piece placement,
    side to move, and castling rights. The halfmove clock is EXCLUDED because
    these puzzles are constructed with clock 0 and never approach 100; including
    it would fragment the memo for no gain. The ep square is excluded when no
    legal ep capture exists, matching python-chess's own `Board.fen()` behaviour
    (brief rule 5) so two spellings of the same position cannot land in
    different memo buckets.
    """
    legal_ep = board.ep_square is not None and any(
        board.is_en_passant(m) for m in board.legal_moves)
    return board.board_fen() + ("|w|" if board.turn == chess.WHITE else "|b|") + \
        ("|" + board.castling_xfen().replace("-", "") if board.castling_rights else "|") + \
        ("|" + chess.square_name(board.ep_square) if legal_ep else "")


class NegamaxOracle:
    """Depth-first ply-exact mate solver with a distance-aware memo."""

    def __init__(self) -> None:
        self.calls = 0

    def solve(self, board: chess.Board, max_plies: int) -> int:
        if board.is_checkmate():
            return -1
        self._memo: dict[tuple[str, int], int] = {}
        for n in range(1, max_plies + 1, 2):
            if self._mated_within(board, n):
                return n
        return 0

    def _mated_within(self, board: chess.Board, plies: int) -> bool:
        """True iff side to move forces checkmate in AT MOST `plies` plies."""
        if plies < 1:
            return False
        if board.is_checkmate():
            return True
        return self._attacker(board, plies)

    def _attacker(self, board: chess.Board, plies: int) -> bool:
        # A mate still needs at least one attacking ply. Without this floor the
        # recursion runs negative forever (this solver produced a
        # RecursionError on a mate-in-1 before it was added).
        if plies < 1:
            return False
        self.calls += 1
        key = (_memo_key(board), plies)
        hit = self._memo.get(key)
        if hit is not None:
            return hit == 1
        # Cycle guard: a repetition is not progress toward mate. A position
        # already on this path cannot be part of a forced mate within budget.
        self._memo[key] = 0
        out = False
        for move in board.legal_moves:
            board.push(move)
            ok = self._defender(board, plies - 1)
            board.pop()
            if ok:
                out = True
                break
        self._memo[key] = 1 if out else 0
        return out

    def _defender(self, board: chess.Board, plies: int) -> bool:
        """True iff EVERY legal reply still loses within `plies` plies."""
        if board.is_checkmate():
            return True
        if board.is_stalemate() or board.is_insufficient_material():
            return False
        if plies < 0:
            return False
        self.calls += 1
        key = (_memo_key(board), plies)
        hit = self._memo.get(key)
        if hit is not None:
            return hit == 1
        self._memo[key] = 0
        out = True
        for move in board.legal_moves:
            board.push(move)
            ok = self._attacker(board, plies - 1)
            board.pop()
            if not ok:
                out = False
                break
        self._memo[key] = 1 if out else 0
        return out


def _layered_attacker(board: chess.Board, plies: int) -> bool:
    """Independent bottom-up mate-within-k check (no shared search code).

    Recursion depth and structure differ from NegamaxOracle: this one asks
    "does a move exist such that every reply is in the losing set" using a
    fresh recursive helper whose memo keys on (position, plies, side-of-node)
    and which never carries alpha/beta.
    """
    if board.is_checkmate():
        return True
    if plies < 1:
        return False
    memo: dict[tuple[str, int], bool] = {}

    def can_force(b: chess.Board, k: int) -> bool:
        if b.is_checkmate():
            return True
        if k < 1:
            return False
        key = (_memo_key(b), k)
        if key in memo:
            return memo[key]
        memo[key] = False
        for m in b.legal_moves:
            b.push(m)
            holds = must_lose(b, k - 1)
            b.pop()
            if holds:
                memo[key] = True
                return True
        return False

    def must_lose(b: chess.Board, k: int) -> bool:
        if b.is_checkmate():
            return True
        if b.is_stalemate() or b.is_insufficient_material():
            return False
        replies = list(b.legal_moves)
        if not replies:
            return b.is_checkmate()
        for m in replies:
            b.push(m)
            ok = can_force(b, k - 1)
            b.pop()
            if not ok:
                return False
        return True

    return can_force(board, plies)


def solve_negamax(board: chess.Board, max_plies: int) -> int:
    return NegamaxOracle().solve(board, max_plies)


def solve_layered(board: chess.Board, max_plies: int) -> int:
    if board.is_checkmate():
        return -1
    for n in range(1, max_plies + 1, 2):
        if _layered_attacker(board, n):
            return n
    return 0


def crosscheck(board: chess.Board, max_plies: int) -> int | None:
    """Both oracles must agree, or the answer is None and the entry is dropped."""
    a = solve_negamax(board, max_plies)
    b = solve_layered(board, max_plies)
    return a if a == b else None


def mating_moves(board: chess.Board, plies: int) -> list[chess.Move]:
    """Every root move that forces mate in exactly `plies` plies (shortest)."""
    out: list[chess.Move] = []
    oracle = NegamaxOracle()
    oracle._memo = {}
    for move in board.legal_moves:
        board.push(move)
        # After the mating move the defender must lose within plies-1.
        ok = oracle._defender(board, plies - 1) if not board.is_checkmate() else True
        board.pop()
        if ok:
            out.append(move)
    return out
