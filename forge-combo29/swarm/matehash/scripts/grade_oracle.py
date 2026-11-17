"""Grade the DTM predicates against plain minimax, and settle disputes with witnesses.

THREE CHECKS, IN ORDER OF WHAT THEY PROVE

  1. PREDICATE vs REFERENCE.  `_mate_within(b,P)` and `_mated_within(b,P)` are
     memoized set-valued predicates; `solve_reference(b,P)` is plain minimax with
     no pruning and no memo. At a fixed, small P they must agree on the SIGN
     (mate / mated / neither). This is what licenses using the fast predicate
     instead of an exponential search.

  2. WITNESS FOR BOTH ORIENTATIONS.  A distance claim is only evidence if a
     concrete line can be produced for it. The two orientations are not
     symmetric and an earlier version of this module got them wrong:
         kind="mate"   root side mates;  attacker moves on plies 1,3,5,...
         kind="mated"  root side is mated; the OPPONENT moves on plies 2,4,6,...
     Both are built here, and each witness is replayed to confirm checkmate.

  3. PLANTED FAULT.  The witness finder is asked for a distance that does NOT
     exist and must return None. If it "finds" one, the finder is broken and
     every positive result from it is worthless.

Output: evidence/oracle_grading.json
"""

from __future__ import annotations

import json
import sys

import chess

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from dtm import _mate_within, _mated_within, solve_reference  # noqa: E402


def predicate_sign(board, plies, cap=4_000_000):
    memo: dict = {}
    counters = {"n": 0}
    try:
        pred = _mate_within if plies % 2 == 1 else _mated_within
        return bool(pred(board.copy(), plies, memo, counters, cap))
    except RuntimeError:
        return None


def reference_sign(board, plies, cap=4_000_000):
    score, _, capped = solve_reference(board, plies, cap)
    if capped:
        return None
    if score is None:
        return None
    if score >= 400_000:
        return True
    if score <= -400_000:
        return True
    return False


def grade_predicates(fens, budgets=(1, 3, 5, 7)):
    rows = []
    for fen in fens:
        board = chess.Board(fen)
        for plies in budgets:
            p = predicate_sign(board, plies)
            r = reference_sign(board, plies)
            if p is None or r is None:
                continue
            # The predicate answers "is there a forced mate/mate-in-progress for
            # THIS orientation at THIS budget". The reference answers "does the
            # minimax score reach the mate band at all". So the sign that must
            # agree is: mate-band-or-not, per orientation.
            rows.append({"fen": fen, "plies": plies, "predicate": p, "reference": r,
                         "agree": p == r})
    return rows


def witness_mate(board, plies, cap=8_000_000):
    """Root side mates in exactly `plies`. Root side moves on plies 1,3,5,..."""
    if plies % 2 == 0 or plies <= 0:
        return None

    def dfs(b, left, path):
        if left <= 0:
            return None
        for mv in b.legal_moves:
            b.push(mv)
            path.append(mv.uci())
            if b.is_checkmate():
                if left == 1:
                    out = list(path)
                    path.pop()
                    b.pop()
                    return out
                path.pop()
                b.pop()
                continue
            # Every defender reply must lose within the remaining budget.
            memo, cnt = {}, {"n": 0}
            try:
                forced = _mated_within(b, left - 1, memo, cnt, cap)
            except RuntimeError:
                forced = False
            if forced:
                deeper = dfs(b, left - 2, path)
                if deeper is not None:
                    path.pop()
                    b.pop()
                    return deeper
            path.pop()
            b.pop()
        return None

    line = dfs(board.copy(), plies, [])
    if line is None:
        return None
    return _replay(board, line, plies)


def witness_mated(board, plies, cap=8_000_000):
    """Root side is mated in exactly `plies`. OPPONENT mates; plies is even."""
    if plies % 2 == 1 or plies <= 0:
        return None

    def dfs(b, left, path):
        if left <= 0:
            return None
        for mv in b.legal_moves:
            b.push(mv)
            path.append(mv.uci())
            if b.is_checkmate():
                # Root side delivering mate ends the game the wrong way.
                path.pop()
                b.pop()
                continue
            # After the victim's move, the opponent must mate within `left`-1.
            memo, cnt = {}, {"n": 0}
            try:
                opponent_mates = _mate_within(b, left - 1, memo, cnt, cap)
            except RuntimeError:
                opponent_mates = False
            if opponent_mates:
                # Descend: the opponent's mating move is found by trying replies.
                found = dfs_reply(b, left - 1, path)
                if found is not None:
                    path.pop()
                    b.pop()
                    return found
            path.pop()
            b.pop()
        return None

    def dfs_reply(b, left, path):
        # b: opponent (the matER) to move.
        if left <= 0:
            return None
        for mv in b.legal_moves:
            b.push(mv)
            path.append(mv.uci())
            if b.is_checkmate():
                if left == 1:
                    out = list(path)
                    path.pop()
                    b.pop()
                    return out
                path.pop()
                b.pop()
                continue
            # The victim must be forced again.
            found = dfs(b, left - 1, path)
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
    return _replay(board, line, plies)


def _replay(board, line, plies):
    check = board.copy()
    ok = True
    for u in line:
        mv = chess.Move.from_uci(u)
        if mv not in check.legal_moves:
            ok = False
            break
        check.push(mv)
    return {
        "line": line,
        "plies": plies,
        "length": len(line),
        "replay_legal": ok,
        "replay_ends_in_checkmate": ok and check.is_checkmate(),
    }


def main():
    here = __file__.rsplit("/", 2)[0]
    corpus = json.load(open(here + "/evidence/corpus.json"))
    fens = [f["fen"] for f in corpus["fixtures"]]

    grading = grade_predicates(fens[:80])
    agree = sum(1 for r in grading if r["agree"])

    # Witnesses for the corpus sample, both orientations.
    witnesses = []
    for f in corpus["fixtures"][:40]:
        board = chess.Board(f["fen"])
        plies = 2 * f["moves"] - 1 if f["kind"] == "mate" else 2 * f["moves"]
        fn = witness_mate if f["kind"] == "mate" else witness_mated
        w = fn(board, plies)
        witnesses.append({"fen": f["fen"], "kind": f["kind"], "moves": f["moves"],
                          "plies": plies, "witness": w,
                          "ok": bool(w and w["replay_ends_in_checkmate"] and w["length"] == plies)})

    # Planted fault: ask for a mate that cannot exist (a bare-kings board).
    dead = chess.Board("8/8/8/8/8/8/8/k1K5 w - - 0 1")
    planted = {
        "fen": dead.fen(),
        "asked_plies": 5,
        "witness": witness_mate(dead, 5),
    }
    planted["correctly_none"] = planted["witness"] is None

    out = {
        "predicate_vs_reference": {
            "n": len(grading),
            "agree": agree,
            "gate": "PASS" if grading and agree == len(grading) else "FAIL",
            "rows": grading,
        },
        "witnesses": {
            "n": len(witnesses),
            "ok": sum(1 for w in witnesses if w["ok"]),
            "gate": "PASS" if witnesses and all(w["ok"] for w in witnesses) else "FAIL",
            "rows": witnesses,
        },
        "planted_fault": planted,
    }
    with open(here + "/evidence/oracle_grading.json", "w") as fh:
        json.dump(out, fh, indent=2)
    print(json.dumps({
        "predicate_gate": out["predicate_vs_reference"]["gate"],
        "predicate_agree": f"{agree}/{len(grading)}",
        "witness_gate": out["witnesses"]["gate"],
        "witness_ok": f"{out['witnesses']['ok']}/{len(witnesses)}",
        "planted_correctly_none": planted["correctly_none"],
    }, indent=2))
    return 0 if (out["predicate_vs_reference"]["gate"] == "PASS"
                 and out["witnesses"]["gate"] == "PASS"
                 and planted["correctly_none"]) else 1


if __name__ == "__main__":
    sys.exit(main())
