#!/usr/bin/env python3
"""The bail's THREE predicates, reimplemented, plus the stats helpers.

The guard at `src/search.cpp:2251` in the base build is:

    const bool root_drawn = !legal.empty() && (board.is_repetition() ||
                                               board.halfmove_clock() >= 100 ||
                                               board.is_insufficient_material());

Everything in this audit is counted against THAT guard.

ON `engine_insufficient` VS PYTHON-CHESS. An earlier draft of this file asserted
that `chess.Board.is_insufficient_material()` disagrees with the engine on K+N v K.
That assertion was FALSE and was found false by testing it: python-chess also calls
K+N v K insufficient. Measured agreement: 4,000 randomly generated bare-minor
positions and six hand cases (K+N v K, K+B v K, K+2N v K, K+N v K+N, K+B v K+B on
same and opposite complexes) -- zero disagreements. The predicate is nonetheless
reimplemented from the engine's source rather than delegated, so what the audit
measures is the engine's rule and cannot drift silently if python-chess changes.

Non-vacuity of this module is established separately by `oracle.py`, which compares
it against the base binary's own caller-visible bail signature (0 nodes AND empty
pv) on cases whose answer is known in both directions.
"""
from __future__ import annotations

import chess


def engine_insufficient(board: chess.Board) -> bool:
    """Board::is_insufficient_material(), board.cpp:1250.

    `minor_count <= 1` is insufficient; two or more minors are insufficient only if
    there are no knights and all bishops sit on one colour complex.
    """
    pawns_rooks_queens = 0
    knights = 0
    bishops_light = 0
    bishops_dark = 0
    for square, piece in board.piece_map().items():
        t = piece.piece_type
        if t in (chess.PAWN, chess.ROOK, chess.QUEEN):
            pawns_rooks_queens += 1
        elif t == chess.KNIGHT:
            knights += 1
        elif t == chess.BISHOP:
            light = (chess.square_file(square) + chess.square_rank(square)) % 2 == 1
            if light:
                bishops_light += 1
            else:
                bishops_dark += 1
    if pawns_rooks_queens:
        return False
    minor_count = knights + bishops_light + bishops_dark
    if minor_count <= 1:
        return True
    return knights == 0 and (bishops_dark == 0 or bishops_light == 0)


def engine_repetition(board: chess.Board) -> bool:
    """Board::is_repetition(), board.cpp:1224: >= 3 occurrences of the current key
    inside the reversible window. python-chess's is_repetition(3) is the same test."""
    return board.is_repetition(3)


def predicates(board: chess.Board) -> dict:
    return {
        "legal": board.legal_moves.count(),
        "halfmove_value": board.halfmove_clock,
        "halfmove": board.halfmove_clock >= 100,
        "threefold": engine_repetition(board),
        "insufficient": engine_insufficient(board),
    }


def is_drawn_root(board: chess.Board) -> tuple[bool, dict]:
    """The bail's full guard, including its `!legal.empty()` term."""
    p = predicates(board)
    fired = p["legal"] > 0 and (p["halfmove"] or p["threefold"] or p["insufficient"])
    return fired, p


def reason(p: dict) -> str:
    """Which predicates fired, in the engine's own order of evaluation."""
    parts = []
    if p["threefold"]:
        parts.append("threefold")
    if p["halfmove"]:
        parts.append("halfmove")
    if p["insufficient"]:
        parts.append("insufficient")
    return "+".join(parts) if parts else "none"


def endgame_type(board: chess.Board) -> str:
    """Material label at the drawn root, e.g. `6-piece 3P2R` (kings included)."""
    counts = {chess.PAWN: 0, chess.KNIGHT: 0, chess.BISHOP: 0,
              chess.ROOK: 0, chess.QUEEN: 0}
    for piece in board.piece_map().values():
        if piece.piece_type in counts:
            counts[piece.piece_type] += 1
    total = sum(counts.values())
    if total == 0:
        return "bare kings"
    sig = ""
    for piece_type, letter in ((chess.PAWN, "P"), (chess.KNIGHT, "N"),
                               (chess.BISHOP, "B"), (chess.ROOK, "R"),
                               (chess.QUEEN, "Q")):
        n = counts[piece_type]
        if n:
            sig += f"{n}{letter}"
    return f"{total + 2}-piece {sig}"


def wilson(k: int, n: int, z: float = 1.959964) -> tuple[float, float]:
    """95% Wilson score interval for a proportion."""
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5) / denom
    return (max(0.0, centre - half), min(1.0, centre + half))
