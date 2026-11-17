"""The engine's drawn-root predicate, reimplemented, plus an oracle that proves it.

The engine bails at the root when `board.is_repetition() || halfmove_clock >= 100 ||
is_insufficient_material()` (search.cpp:2251-2253). On a bail it returns 0 nodes, an
empty pv, and plays the generator's first move UNSEARCHED.

That predicate cannot be exercised by a driver that only sends FENs: the repetition
arm needs the same position three times in the MOVE LIST, which is exactly what a
GUI sends and what a FEN cannot express. So the driver sends `position fen X moves
...` and this module predicts the arm from the same history.

WHY REIMPLEMENT RATHER THAN READ THE SCORE. The bail prints `cp 0` with 0 nodes, and
`cp 0` is also a legitimate score for a drawn position that WAS searched. Node count
is what separates them, so the prediction is checked against nodes, never against
the score.

Semantics: python-chess `Board.is_repetition(n)` counts OCCURRENCES of the current
position in the history INCLUDING the current one, so `is_repetition(3)` is a genuine
threefold. The engine's own rule is the same shape but counts from the root's history
index; see oracle.py, which proves the prediction against the binary instead of
arguing about it.
"""
from __future__ import annotations

import chess


def clock_reason(board: chess.Board):
    """Which arm of the engine's drawn-root predicate fires, or None."""
    if board.is_repetition(3):
        return "repetition"
    if board.halfmove_clock >= 100:
        return "fifty"
    if board.is_insufficient_material():
        return "material"
    return None


def bailed(result: dict) -> bool:
    """A bail is 0 nodes AND an empty pv on a position that was not terminal.

    Both tests are required: a 0-node root with a pv would be a different defect,
    and a terminal root is not a bail at all.
    """
    from uci import parse_info
    if not result.get("last"):
        # no info line at all: the engine printed only bestmove
        return True
    pi = parse_info(result["last"])
    return pi.get("nodes", 0) == 0 and not pi.get("pv")
