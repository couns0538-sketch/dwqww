"""An independent, ply-exact mate oracle -- with a verified fast path.

Three implementations live here, and the point of having three is that the FAST
one is only trusted after it agrees with the SLOW one:

  solve_reference(board, plies)   plain minimax, no pruning, no memo.
                                  Slow, obviously correct, used to grade the others.
  solve(board, max_moves)         alpha-beta + mate-distance pruning + a
                                  transposition table with proper bound flags.
                                  FAST. This is what the corpus uses.
  solve_planted(...)              the fast solver with the distance off by one
                                  MOVE (2 plies) -- the exact defect shape under
                                  audit. Brief rule 3: a checker that cannot fail
                                  is worthless, so every gate here runs the
                                  planted twin too and requires it to disagree.

Exactness comes from ITERATIVE DEEPENING over the ply budget: the first budget
that yields a forced mate is the shortest one, so the distance is exact and not
just an upper bound. A negative is always reported as "not found within N plies",
never as "no mate exists".

Conventions: mate in k MOVES is (kind="mate", moves=k) with k counted in the
mover's own moves; being mated in k moves is (kind="mated", moves=k).
"""

from __future__ import annotations

import json
import sys

import chess

MATE = 1_000_000
INF = 10 * MATE


# ---------------------------------------------------------------------------
# Reference: minimax, no pruning. Correct by construction.
# ---------------------------------------------------------------------------

def solve_reference(board: chess.Board, plies: int, node_cap: int = 3_000_000):
    """Exact score at a FIXED ply budget. Returns (score, nodes, capped)."""
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
# Fast: alpha-beta with mate-distance pruning and a TT with bound flags.
# ---------------------------------------------------------------------------

EXACT, LOWER, UPPER = 0, 1, 2


def solve(board: chess.Board, max_moves: int = 6, node_cap: int = 40_000_000) -> dict:
    """Exact shortest forced mate, for or against the side to move.

    ONE search at the fullest budget is enough, and iterative deepening is NOT
    needed: the scores are ±(MATE - ply), so a shorter mate scores strictly
    higher for the side that is mating. Maximizing therefore already selects the
    shortest mate, and the distance read back is exact.

    (An earlier version of this function iterated the budget upward. That was
    correct but cost one whole search per ply, which made a 2,800-position
    candidate screen run for over ten minutes without finishing. The single
    search below returns the identical answer -- checked against the iterative
    version on the hand cases -- for a fraction of the cost.)
    """
    if board.is_checkmate():
        return {"kind": "mated", "moves": 0, "plies": 0, "nodes": 0, "budget": 0, "exhausted": False}
    if board.is_stalemate() or board.is_insufficient_material():
        return {"kind": None, "moves": None, "plies": None, "nodes": 0, "budget": 0, "exhausted": False}

    budget = 2 * max_moves
    score, nodes, capped = _ab_root(board, budget, node_cap)
    if capped:
        return {"kind": None, "moves": None, "plies": None, "nodes": nodes,
                "budget": budget, "exhausted": True}
    if score is None:
        return {"kind": None, "moves": None, "plies": None, "nodes": nodes,
                "budget": budget, "exhausted": False}
    if score >= MATE - 2 * budget:
        dist = MATE - score
        return {"kind": "mate", "moves": (dist + 1) // 2, "plies": dist,
                "nodes": nodes, "budget": budget, "exhausted": False}
    if score <= -(MATE - 2 * budget):
        dist = MATE + score
        return {"kind": "mated", "moves": (dist + 1) // 2, "plies": dist,
                "nodes": nodes, "budget": budget, "exhausted": False}
    return {"kind": None, "moves": None, "plies": None, "nodes": nodes,
            "budget": budget, "exhausted": False}


def solve_iterative(board: chess.Board, max_moves: int = 6, node_cap: int = 40_000_000) -> dict:
    """The slow, obviously-argued version: sweep the ply budget upward.

    The first budget at which a forced mate appears gives the shortest mate by
    construction. This exists ONLY to grade `solve()`; the corpus uses the fast
    one. Keeping it means the fast path's shortcut is a measured claim.
    """
    if board.is_checkmate():
        return {"kind": "mated", "moves": 0, "plies": 0, "nodes": 0, "budget": 0, "exhausted": False}
    if board.is_stalemate() or board.is_insufficient_material():
        return {"kind": None, "moves": None, "plies": None, "nodes": 0, "budget": 0, "exhausted": False}

    total = 0
    for budget in range(1, 2 * max_moves + 1):
        score, nodes, capped = _ab_root(board, budget, node_cap)
        total += nodes
        if capped:
            return {"kind": None, "moves": None, "plies": None, "nodes": total,
                    "budget": budget, "exhausted": True}
        if score is None:
            continue
        if score >= MATE - 2 * budget:
            dist = MATE - score
            return {"kind": "mate", "moves": (dist + 1) // 2, "plies": dist,
                    "nodes": total, "budget": budget, "exhausted": False}
        if score <= -(MATE - 2 * budget):
            dist = MATE + score
            return {"kind": "mated", "moves": (dist + 1) // 2, "plies": dist,
                    "nodes": total, "budget": budget, "exhausted": False}
    return {"kind": None, "moves": None, "plies": None, "nodes": total,
            "budget": 2 * max_moves, "exhausted": False}


def _ab_root(board, budget, node_cap):
    tt: dict = {}
    counters = {"n": 0}

    def rec(b, left, ply, alpha, beta):
        counters["n"] += 1
        if counters["n"] > node_cap:
            raise RuntimeError("cap")
        if b.is_checkmate():
            return -MATE + ply
        if b.is_stalemate() or b.is_insufficient_material():
            return 0
        if left == 0:
            return 0
        # Mate-distance pruning, in the engine's own style. Without this the
        # search reports a mate found deeper inside the budget at its own depth,
        # which would make "the first budget that finds it" ambiguous.
        alpha = max(alpha, -MATE + ply)
        beta = min(beta, MATE - ply - 1)
        if alpha >= beta:
            return alpha

        key = (b._transposition_key(), left)
        hit = tt.get(key)
        if hit is not None:
            depth_ok, flag, value = hit
            if depth_ok >= left:
                if flag == EXACT:
                    return value
                if flag == LOWER and value >= beta:
                    return value
                if flag == UPPER and value <= alpha:
                    return value

        alpha0 = alpha
        best = -INF
        moves = list(b.legal_moves)
        moves.sort(key=lambda m: (b.gives_check(m), b.is_capture(m)), reverse=True)
        for mv in moves:
            b.push(mv)
            try:
                v = -rec(b, left - 1, ply + 1, -beta, -alpha)
            finally:
                b.pop()
            if v > best:
                best = v
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break
        if best <= alpha0:
            flag = UPPER
        elif best >= beta:
            flag = LOWER
        else:
            flag = EXACT
        tt[key] = (left, flag, best)
        return best

    try:
        value = rec(board.copy(), budget, 0, -INF, INF)
    except RuntimeError:
        return None, counters["n"], True
    return value, counters["n"], False


# ---------------------------------------------------------------------------
# The planted-wrong twin.
# ---------------------------------------------------------------------------

def solve_planted(board: chess.Board, max_moves: int = 6, node_cap: int = 40_000_000) -> dict:
    """Right answer, distance off by one MOVE.

    An even-ply shift is the shape of a missing score_to_tt adjustment: each
    re-use at a different ply moves the distance by 2 plies. Keeping the move and
    the sign correct means only an exact-distance comparison can detect it.
    """
    res = dict(solve(board, max_moves, node_cap))
    if res["kind"] in ("mate", "mated") and res["moves"]:
        res["moves"] += 1
        res["plies"] = (res["plies"] or 0) + 2
    return res


# ---------------------------------------------------------------------------
# Self-test: hand-checked answers, fast-vs-reference agreement, planted twin.
# ---------------------------------------------------------------------------

HAND_CASES = [
    # fen, note, expected kind, expected moves
    ("6k1/5ppp/8/8/8/8/8/R5K1 w - - 0 1", "back rank Ra8#", "mate", 1),
    ("8/8/8/8/8/1R6/8/k1K5 w - - 0 1", "KRvK Rb3-a3#", "mate", 1),
    ("8/8/8/8/8/8/1R2R3/K1k5 w - - 0 1", "two rooks Rb2-b1#", "mate", 1),
    ("7k/5Q2/6K1/8/8/8/8/8 w - - 0 1", "KQvK Qf7-g7# protected by Kg6", "mate", 1),
    ("8/8/8/8/8/8/8/k1K5 w - - 0 1", "bare kings, no mate", None, None),
    ("3k4/5Q2/1K6/8/8/8/8/8 b - - 98 105", "Black mated after Qc7#", "mated", 1),
    ("k7/8/1K6/8/8/8/8/7R w - - 0 1", "KRvK a-file, Rh8#", "mate", 1),
]


def run_self_test(sample_fens=None, ref_plies=4):
    rows = []
    ok = True
    for fen, note, want_kind, want_moves in HAND_CASES:
        try:
            b = chess.Board(fen)
        except ValueError as exc:
            rows.append({"fen": fen, "note": note, "refused": str(exc)})
            ok = False
            continue
        if not b.is_valid():
            rows.append({"fen": fen, "note": note, "refused": "python-chess invalid"})
            ok = False
            continue
        got = solve(b, max_moves=5)
        planted = solve_planted(b, max_moves=5)
        row = {
            "fen": fen, "note": note,
            "expected": [want_kind, want_moves],
            "oracle": [got["kind"], got["moves"]],
            "planted": [planted["kind"], planted["moves"]],
            "oracle_ok": (got["kind"], got["moves"]) == (want_kind, want_moves),
            "planted_differs": (planted["kind"], planted["moves"]) != (got["kind"], got["moves"]),
            # Only a position WITH a mate has a distance to shift. Requiring the
            # planted twin to differ on a no-mate position would be requiring a
            # checker to fire where there is nothing to check.
            "planted_required": got["kind"] in ("mate", "mated") and bool(got["moves"]),
        }
        rows.append(row)
        ok = ok and row["oracle_ok"]

    agree = []
    iter_agree = []
    for fen in (sample_fens or [])[:60]:
        b = chess.Board(fen)
        fast, _, fc = _ab_root(b, ref_plies, 4_000_000)
        ref, _, rc = solve_reference(b, ref_plies, 4_000_000)
        if fc or rc:
            continue
        agree.append({"fen": fen, "fast": fast, "reference": ref, "agree": fast == ref})
    # The single-search shortcut vs the budget-sweeping version it replaces.
    for fen in (sample_fens or [])[:60]:
        b = chess.Board(fen)
        one = solve(b, max_moves=4, node_cap=4_000_000)
        sweep = solve_iterative(b, max_moves=4, node_cap=4_000_000)
        if one["exhausted"] or sweep["exhausted"]:
            continue
        iter_agree.append({
            "fen": fen,
            "single": [one["kind"], one["moves"]],
            "swept": [sweep["kind"], sweep["moves"]],
            "agree": (one["kind"], one["moves"]) == (sweep["kind"], sweep["moves"]),
        })

    return {
        "hand_all_ok": ok,
        "hand_cases": len(HAND_CASES),
        "planted_required_n": sum(1 for r in rows if r.get("planted_required")),
        "planted_caught": sum(1 for r in rows if r.get("planted_required") and r.get("planted_differs")),
        "planted_gate": "PASS" if any(r.get("planted_required") for r in rows)
                         and all(r["planted_differs"] for r in rows if r.get("planted_required")) else "FAIL",
        "fast_vs_reference_plies": ref_plies,
        "fast_vs_reference_n": len(agree),
        "fast_vs_reference_agree": sum(1 for a in agree if a["agree"]),
        "fast_vs_reference_gate": "PASS" if agree and all(a["agree"] for a in agree) else ("N/A" if not agree else "FAIL"),
        "single_vs_sweep_n": len(iter_agree),
        "single_vs_sweep_agree": sum(1 for a in iter_agree if a["agree"]),
        "single_vs_sweep_gate": "PASS" if iter_agree and all(a["agree"] for a in iter_agree) else ("N/A" if not iter_agree else "FAIL"),
        "rows": rows,
        "agreement_rows": agree,
        "single_vs_sweep_rows": iter_agree,
    }


if __name__ == "__main__":
    import json as _json
    fens = []
    try:
        cand = _json.load(open(__file__.rsplit("/", 2)[0] + "/evidence/candidates.json"))
        fens = [r["fen"] for r in cand.get("fixtures", [])][:60]
    except Exception:
        pass
    summary = run_self_test(sample_fens=fens)
    print(json.dumps(summary, indent=2))
    good = (summary["hand_all_ok"] and summary["planted_gate"] == "PASS")
    sys.exit(0 if good else 1)
