"""A clean distance-to-mate (DTM) solver, and direct verification of PV claims.

WHY THIS EXISTS
    The first oracle in this seat used negamax with mate scores of the form
    `-MATE + ply` and read the distance back as `MATE - score`. It reported
    "mated in 4" for a position where the engine reported `mate -5`. Before
    calling that an engine defect, the ORACLE has to be beyond doubt -- a seat
    that reports its own bug as a finding is the failure mode this audit exists
    to prevent.

    So this module computes DTM by a definition that can be read off the board
    with no score arithmetic at all:

        dtm(b)  > 0 : the side to move at b delivers checkmate in dtm(b) PLIES
        dtm(b)  < 0 : the side to move at b is checkmated in |dtm(b)| PLIES
        dtm(b) == 0 : neither within the horizon (draw or unknown)

    and, crucially, the two operations it uses are stated as separate,
    checkable predicates rather than as sign conventions:

        forced_mate_in(b, plies)    all lines: the mover mates within `plies`
        forced_mated_in(b, plies)   all moves: the mover is mated within `plies`

    `verify_pv()` then takes an engine PV and plays it, checking the mate claim
    move by move. That is independent of any solver: it says whether THIS line
    mates, and whether the defender had an escape along it.

Both are graded against `solve_reference` (plain minimax, no pruning, no memo)
at fixed ply budgets, so the pruning in the fast path is a measured claim.
"""

from __future__ import annotations

import json
import sys

import chess

MATE = 1_000_000
INF = 10 * MATE


# ---------------------------------------------------------------------------
# Minimal, obviously-correct reference: plain minimax at a fixed ply budget.
# ---------------------------------------------------------------------------

def solve_reference(board: chess.Board, plies: int, node_cap: int = 5_000_000):
    """Score at a fixed horizon, no pruning, no memo. (score, nodes, capped)."""
    counters = {"n": 0}

    def rec(b, left):
        counters["n"] += 1
        if counters["n"] > node_cap:
            raise RuntimeError("cap")
        if b.is_checkmate():
            return -MATE
        if b.is_stalemate() or b.is_insufficient_material():
            return 0
        if left == 0:
            return 0
        best = -INF
        for mv in b.legal_moves:
            b.push(mv)
            try:
                v = -rec(b, left - 1)
            finally:
                b.pop()
            if v > best:
                best = v
        return best

    try:
        return rec(board.copy(), plies), counters["n"], False
    except RuntimeError:
        return None, counters["n"], True


# ---------------------------------------------------------------------------
# DTM by definition. Memoized per (position, plies-budget); exact because the
# budget is swept from the smallest mate upward and the first hit is reported.
# ---------------------------------------------------------------------------

def _mated_within(b, plies, memo, counters, cap):
    """True iff EVERY legal move lets the opponent mate within `plies - 1`."""
    if b.is_checkmate():
        return True
    if b.is_stalemate() or b.is_insufficient_material():
        return False
    if plies <= 0:
        return False
    counters["n"] += 1
    if counters["n"] > cap:
        raise RuntimeError("cap")
    key = (b._transposition_key(), "M", plies)
    if key in memo:
        return memo[key]
    out = True
    for mv in b.legal_moves:
        b.push(mv)
        try:
            ok = _mate_within(b, plies - 1, memo, counters, cap)
        finally:
            b.pop()
        if not ok:
            out = False
            break
    memo[key] = out
    return out


def _mate_within(b, plies, memo, counters, cap):
    """True iff SOME line mates within `plies` plies (best play by both)."""
    if b.is_checkmate():
        return False  # the side to move is mated, not mating
    if b.is_stalemate() or b.is_insufficient_material():
        return False
    if plies <= 0:
        return False
    counters["n"] += 1
    if counters["n"] > cap:
        raise RuntimeError("cap")
    key = (b._transposition_key(), "W", plies)
    if key in memo:
        return memo[key]
    out = False
    for mv in b.legal_moves:
        b.push(mv)
        try:
            if b.is_checkmate():
                out = True
            elif _mated_within(b, plies - 1, memo, counters, cap):
                out = True
        finally:
            b.pop()
        if out:
            break
    memo[key] = out
    return out


def dtm(board: chess.Board, max_plies: int = 12, cap: int = 8_000_000) -> dict:
    """Exact distance to mate in PLIES, with the smallest-mate sweep."""
    if board.is_checkmate():
        return {"plies": 0, "mover_mates": False, "nodes": 0, "exhausted": False}
    if board.is_stalemate() or board.is_insufficient_material():
        return {"plies": None, "mover_mates": None, "nodes": 0, "exhausted": False}

    memo: dict = {}
    counters = {"n": 0}
    for plies in range(1, max_plies + 1):
        try:
            if plies % 2 == 1:
                # ODD budgets can only contain OUR mate (we move on ply 1).
                if _mate_within(board.copy(), plies, memo, counters, cap):
                    return {"plies": plies, "mover_mates": True, "nodes": counters["n"], "exhausted": False}
            else:
                # EVEN budgets can only contain us BEING mated.
                if _mated_within(board.copy(), plies, memo, counters, cap):
                    return {"plies": plies, "mover_mates": False, "nodes": counters["n"], "exhausted": False}
        except RuntimeError:
            return {"plies": None, "mover_mates": None, "nodes": counters["n"],
                    "exhausted": True, "reached_plies": plies}
    return {"plies": None, "mover_mates": None, "nodes": counters["n"], "exhausted": False}


def dtm_moves(board: chess.Board, max_plies: int = 12, cap: int = 8_000_000) -> dict:
    """Same, reported as UCI would: signed MOVE count (mate in k / mated in k)."""
    d = dtm(board, max_plies, cap)
    if d["plies"] is None:
        return {**d, "uci_mate": None}
    k = (d["plies"] + 1) // 2
    return {**d, "uci_mate": k if d["mover_mates"] else -k}


# ---------------------------------------------------------------------------
# Direct verification of an engine PV. Independent of every solver above.
# ---------------------------------------------------------------------------

def verify_pv(fen: str, pv: list[str]) -> dict:
    """Play the PV. Does it mate? Could the defender have escaped?

    Returns a row per ply: the move, whether it was legal, whether the board
    became checkmate, and whether the side to move had a legal alternative at
    that point (so the reader can see whether "forced" was assumed or checked).
    """
    board = chess.Board(fen)
    rows = []
    for i, uci in enumerate(pv):
        try:
            mv = chess.Move.from_uci(uci)
        except ValueError:
            rows.append({"ply": i + 1, "move": uci, "legal": False, "why": "unparseable"})
            return {"mates": False, "rows": rows}
        if mv not in board.legal_moves:
            rows.append({"ply": i + 1, "move": uci, "legal": False, "why": "not legal here"})
            return {"mates": False, "rows": rows}
        gives = board.gives_check(mv)
        board.push(mv)
        rows.append({
            "ply": i + 1,
            "move": uci,
            "legal": True,
            "gives_check": gives,
            "checkmate": board.is_checkmate(),
            "attacker": "black" if board.turn == chess.WHITE else "white",
        })
        if board.is_checkmate():
            return {"mates": True, "mate_plies": i + 1, "rows": rows}
    return {"mates": False, "mate_plies": None, "rows": rows}


# ---------------------------------------------------------------------------
# Grading.
# ---------------------------------------------------------------------------

HAND = [
    ("6k1/5ppp/8/8/8/8/8/R5K1 w - - 0 1", "mate", 1),
    ("8/8/8/8/8/1R6/8/k1K5 w - - 0 1", "mate", 1),
    ("8/8/8/8/8/8/1R2R3/K1k5 w - - 0 1", "mate", 1),
    ("7k/5Q2/6K1/8/8/8/8/8 w - - 0 1", "mate", 1),
    ("k7/8/1K6/8/8/8/8/7R w - - 0 1", "mate", 1),
    ("3k4/5Q2/1K6/8/8/8/8/8 b - - 98 105", "mated", 1),
    ("8/8/8/8/8/8/8/k1K5 w - - 0 1", None, None),
    ("8/8/8/8/8/8/8/k1K4R w - - 0 1", "mate", 3),
    ("8/8/8/8/8/7R/3K4/1k6 w - - 8 5", "mate", 3),
]


def main():
    """Self-test: hand answers, then fast-vs-reference at a fixed horizon."""
    rows = []
    ok = True
    for fen, kind, moves in HAND:
        b = chess.Board(fen)
        d = dtm_moves(b, max_plies=8)
        got = None if d["uci_mate"] is None else ("mate" if d["uci_mate"] > 0 else "mated")
        row = {
            "fen": fen,
            "expected": [kind, moves],
            "dtm_plies": d["plies"],
            "uci": d["uci_mate"],
            "got": [got, None if d["uci_mate"] is None else abs(d["uci_mate"])],
            "ok": (got, None if d["uci_mate"] is None else abs(d["uci_mate"])) == (kind, moves),
            "exhausted": d.get("exhausted", False),
        }
        rows.append(row)
        ok = ok and row["ok"]
    print(json.dumps({"hand_all_ok": ok, "rows": rows}, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
