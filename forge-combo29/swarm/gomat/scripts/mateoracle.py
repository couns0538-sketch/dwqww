"""Independent mate oracle: exact distance-to-mate by minimax over python-chess.

No fixture in this audit is typed by hand. Positions come from a generator, and
the oracle — not the generator — decides what each one is.

Design notes that matter for honesty:

* `dtm_plies` is exhaustive within its limit, so a `None` is a proof of absence
  *within that window* and is always reported with the window attached, never as
  "no mate exists".
* `no_mate_in_one` is a complete enumeration of the root moves, so it is a proof
  for any position, cheap enough to run on real middlegames.
* The search takes a NODE BUDGET. A candidate that exceeds it is DISCARDED, not
  guessed at. `Oracle.exhausted` says which happened, so a caller cannot mistake
  "budget hit" for "no mate". This is the failure mode findings §6 warns about:
  a control that returns a plausible wrong number passes review.
"""

from __future__ import annotations

import chess


class BudgetExceeded(Exception):
    pass


def _ordering(board: chess.Board) -> list[chess.Move]:
    """Checks first: a mate search finds its witness much sooner.

    This only changes the ORDER of an exhaustive scan, so it cannot change the
    answer — a budgeted run that hits its limit is discarded either way.
    """
    checks = []
    others = []
    for move in board.legal_moves:
        if board.gives_check(move):
            checks.append(move)
        else:
            others.append(move)
    return checks + others


class Oracle:
    def __init__(self, node_budget: int = 3_000_000) -> None:
        self.nodes = 0
        self.budget = node_budget
        self.memo: dict[tuple, int | None] = {}

    def _spend(self) -> None:
        self.nodes += 1
        if self.nodes > self.budget:
            raise BudgetExceeded()

    def _loses_in(self, board: chess.Board, plies: int) -> int | None:
        """Defender to move cannot avoid mate; exact plies until mate, or None."""
        if plies <= 0:
            return None
        if board.is_checkmate():
            return 0
        if board.is_stalemate() or board.is_insufficient_material():
            return None
        key = ("L", board._transposition_key(), plies)
        if key in self.memo:
            return self.memo[key]
        self._spend()

        worst = 0
        for move in board.legal_moves:
            board.push(move)
            if board.is_checkmate():
                sub = 1
            elif board.is_stalemate() or board.is_insufficient_material():
                sub = None
            else:
                inner = self._wins_in(board, plies - 1)
                sub = None if inner is None else inner + 1
            board.pop()
            if sub is None:
                self.memo[key] = None
                return None
            if sub > worst:
                worst = sub
        self.memo[key] = worst
        return worst

    def _wins_in(self, board: chess.Board, plies: int) -> int | None:
        """Attacker to move forces mate; exact plies, or None within the window."""
        if plies <= 0:
            return None
        key = ("W", board._transposition_key(), plies)
        if key in self.memo:
            return self.memo[key]
        self._spend()

        best: int | None = None
        for move in _ordering(board):
            board.push(move)
            if board.is_checkmate():
                sub = 1
            else:
                inner = self._loses_in(board, plies - 1)
                sub = None if inner is None else inner + 1
            board.pop()
            if sub is not None and (best is None or sub < best):
                best = sub
                if best == 1:
                    break
        self.memo[key] = best
        return best

    def dtm_plies(self, board: chess.Board, limit: int) -> int | None:
        """Exact DTM in plies for the side to move, or None if none within `limit`.

        Raises BudgetExceeded when the node budget runs out; the caller must
        discard the position rather than interpret the exception as a result.
        """
        if limit % 2 == 0:
            raise ValueError("limit must be odd (attacker moves on odd plies)")
        return self._wins_in(board, limit)

    def exact_dtm_up_to(self, board: chess.Board, max_k: int) -> int | None:
        """Iterative deepening: exact DTM if the mate is within `max_k` moves.

        Returns the exact ply count, or None if no mate exists within
        2*max_k-1 plies. Because each limit is searched exhaustively and the
        limits are increasing, the first non-None answer is the true minimum.
        """
        for k in range(1, max_k + 1):
            got = self.dtm_plies(board, 2 * k - 1)
            if got is not None:
                return got
        return None


def pv_replays_to_mate(board: chess.Board, uci_moves: list[str]) -> tuple[bool, str]:
    """Replay a PV on a copy of the board; report whether it ends in checkmate."""
    b = board.copy()
    for i, u in enumerate(uci_moves):
        try:
            mv = chess.Move.from_uci(u)
        except ValueError:
            return False, f"unparseable move at index {i}: {u!r}"
        if mv not in b.legal_moves:
            return False, f"illegal move at index {i}: {u}"
        b.push(mv)
    if b.is_checkmate():
        return True, "checkmate"
    return False, f"PV of {len(uci_moves)} plies ends not in mate (in_check={b.is_check()})"


def no_mate_in_one(board: chess.Board) -> bool:
    """Complete proof that the side to move has no mate in one.

    Enumerates every legal move and tests each for immediate checkmate, so this
    is exhaustive over the root, not a sample.
    """
    if board.is_checkmate() or board.is_stalemate():
        return False
    for move in board.legal_moves:
        board.push(move)
        mate = board.is_checkmate()
        board.pop()
        if mate:
            return False
    return True
