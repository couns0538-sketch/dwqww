#!/usr/bin/env python3
"""Independent mate prover, validated against brute-force minimax.

This module exists because the first version of it was WRONG and the audit
nearly recorded the error as an engine finding. Two defects, both of my own:

  1. A transposition table keyed on (position, depth) but NOT on the alpha/beta
     window. A value stored under a narrow window is a bound, and replaying it
     as exact corrupts the search. The table is gone: plain alpha-beta at these
     bounds is fast enough.
  2. Defender-to-move fixtures were built by following ONE reply and calling the
     result a forced mate. A forced mate needs EVERY defence to lose, so those
     fixtures claimed mates that did not exist.

Both were caught by re-running the audit against the base engine and noticing
that the base engine failed 19 of 30 fixtures, which is not a plausible shape
for a correctness bug in the engine under audit.

The prover reports a SIGN as well as a distance:
  +d  the side to move has a forced mate in d plies
  -d  the side to move is mated in d plies whatever it does

`validate.py` checks this module against brute-force minimax on random small
positions, including negative cases, and the audit refuses to run if that check
is not green.
"""

from __future__ import annotations

import chess

MATE = 100000


def ordered(board: chess.Board) -> list[chess.Move]:
    """Checks first, then captures by victim value. Ordering affects speed only:
    the alpha-beta window is what keeps the search a proof."""
    checks, captures, rest = [], [], []
    for move in board.legal_moves:
        if board.gives_check(move):
            checks.append(move)
        elif board.is_capture(move):
            victim = board.piece_at(move.to_square)
            captures.append((victim.piece_type if victim else 0, move))
        else:
            rest.append(move)
    captures.sort(key=lambda t: -t[0])
    return checks + [m for _, m in captures] + rest


class Budget(Exception):
    pass


class Prover:
    """Fail-soft negamax, mate encoded as MATE - ply, no transposition table.

    Only the ROOT value is read, and the root is searched with a full window, so
    every inner bound is used exactly as a bound. That is what makes the root
    value a statement about the whole forced tree.
    """

    def __init__(self, budget: int = 4_000_000) -> None:
        self.nodes = 0
        self.budget = budget

    def search(self, board: chess.Board, depth: int, alpha: int, beta: int, ply: int) -> int:
        self.nodes += 1
        if self.nodes > self.budget:
            raise Budget
        moves = ordered(board)
        if not moves:
            return -MATE + ply if board.is_check() else 0
        if depth <= 0:
            return 0
        # Mate-distance pruning: no mate is faster than this ply or slower than
        # the remaining depth, so anything outside that band is already settled.
        alpha = max(alpha, -MATE + ply)
        beta = min(beta, MATE - ply - 1)
        if alpha >= beta:
            return alpha
        best = -MATE - 1
        for move in moves:
            board.push(move)
            value = -self.search(board, depth - 1, -beta, -alpha, ply + 1)
            board.pop()
            if value > best:
                best = value
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break
        return best


def prove(board: chess.Board, limit: int, budget: int = 4_000_000) -> tuple[int, int] | None:
    """Return (sign, plies) with sign +1 (side to move mates) or -1 (side to move
    is mated), or None if no forced mate is proved within `limit` plies.

    Iterative deepening: the first bound whose score reaches the mate band gives
    the distance, and the previous bound's failure is what proves it is not
    faster. One search is reused across bounds, so nothing is searched twice.
    """
    if board.is_checkmate():
        return (-1, 0)
    if board.is_stalemate() or board.is_insufficient_material():
        return None
    prover = Prover(budget)
    for d in range(1, limit + 1):
        try:
            score = prover.search(board.copy(), d, -MATE - 1, MATE + 1, 0)
        except Budget:
            return None
        if score >= MATE - d:
            return (1, MATE - score)
        if score <= -MATE + d:
            return (-1, MATE + score)
    return None


def rule_clean(board: chess.Board, plies: int) -> bool:
    """A fixture whose "mate" would be cut short by a fifty-move or repetition
    rule cannot test mate handling, so it is rejected rather than adjusted."""
    if board.halfmove_clock + plies >= 100:
        return False
    if board.is_repetition() or board.is_insufficient_material() or board.is_stalemate():
        return False
    return bool(board.legal_moves)


def verify_mate_against_brute(board: chess.Board, limit: int = 5) -> bool:
    """Check `prove` against plain minimax with no pruning at all.

    This is the self-test the audit depends on: it must agree on both signs, and
    it must agree about the ABSENCE of a mate as well.
    """
    def brute(b: chess.Board, depth: int, ply: int = 0) -> int:
        moves = list(b.legal_moves)
        if not moves:
            return -MATE + ply if b.is_check() else 0
        if depth == 0:
            return 0
        best = -MATE - 1
        for m in moves:
            b.push(m)
            v = -brute(b, depth - 1, ply + 1)
            b.pop()
            if v > best:
                best = v
        return best

    got = prove(board, limit)
    want = None
    for d in range(1, limit + 1):
        s = brute(board.copy(), d)
        if s >= MATE - d:
            want = (1, MATE - s)
            break
        if s <= -MATE + d:
            want = (-1, MATE + s)
            break
    return got == want
