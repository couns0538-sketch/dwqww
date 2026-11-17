#!/usr/bin/env python3
"""End-to-end test of the VERIFIER, not just the oracle.

Positions whose exact mate distance is established independently by pysolve
(python-chess negamax, no shared code with the oracle or the engine), then
SYNTHETIC labels:

  HONEST     N = true distance  -> verifier must say EXACT
  OVERSTATE  N = true + 1       -> must say WRONG_OVERSTATED
  OVERSTATE+ N = true + 3       -> must say WRONG_OVERSTATED
  UNDERSTATE N = true - 1       -> must say WRONG_UNDERSTATED

This is brief rule 3 applied to the PIPELINE: if the verifier answers EXACT to a
knowingly wrong label, every clean row in the main run is worthless. S4 records
that the two known-bad boards failed in OPPOSITE directions, so a checker that
only ever reports one direction is not measuring the class -- hence both
directions are planted.

Every synthetic row carries a REAL mating first move, because half (A) pins it.
An earlier draft passed bestmove=None and every wrong-direction case collapsed to
UNVERIFIABLE, which looked like a verifier failure and was a fixture failure --
the same shape as the S4 lesson that a refused fixture manufactures a pass.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import chess
import paths
import pysolve_independent as pysolve
import verify_two_halves as verify

BASE = [
    ("6k1/5ppp/8/8/8/8/8/R5K1 w - - 0 1", "back-rank"),
    ("8/8/8/8/8/2k5/1q6/K7 b - - 0 1", "queen-king"),
    ("7k/6pp/8/8/8/8/6PP/R5K1 w - - 0 1", "back-rank-2"),
    ("2rr3k/pp3pp1/1nnqbN1p/3pN3/2pP4/2P3Q1/PPB4P/R4RK1 w - - 0 1", "wAC"),
    ("r1bq2r1/b4pk1/p1pp1p2/1p2pP2/1P2P1PB/3P4/1PPQ2P1/R3K2R w - - 0 1", "complex"),
    ("r5rk/5p1p/5R2/4B3/8/8/7P/7K w - - 0 1", "quiet-key"),
]


def mating_move(fen, total_plies):
    """A legal first move that mates in exactly `total_plies` plies, or None.

    After the mover's move it is the DEFENDER's turn; the move mates in
    total_plies iff every defender reply loses to a forced mate in
    total_plies-1 from the defender's perspective.
    """
    board = chess.Board(fen)
    for m in board.legal_moves:
        board.push(m)
        ok = False
        if board.is_checkmate():
            ok = (total_plies == 1)
        elif not board.is_game_over():
            s = pysolve.Solver()
            all_lose = True
            for reply in board.legal_moves:
                board.push(reply)
                # attacker to move, needs mate in total_plies-2 plies
                if not s.forces(board, total_plies - 2):
                    all_lose = False
                    board.pop()
                    break
                board.pop()
            ok = all_lose
        board.pop()
        if ok:
            return m
    return None


def main():
    cases = []
    for fen, name in BASE:
        plies, _ = pysolve.exact_plies(fen, 9)
        if plies is None:
            print(f"skip {name}: no mate found")
            continue
        assert plies % 2 == 1, f"{name}: expected odd ply distance for a win"
        mv = mating_move(fen, plies)
        if mv is None:
            print(f"skip {name}: no single move realises the full distance")
            continue
        cases.append((fen, name, (plies + 1) // 2, mv.uci()))

    print(f"base positions with confirmed distance AND a real mating move: {len(cases)}")
    for fen, name, n, mv in cases:
        print(f"  {name:12} true mate in {n}, mating move {mv}")

    expectations = [
        ("HONEST", 0, "EXACT"),
        ("OVERSTATE", +1, "WRONG_OVERSTATED"),
        ("WILD", +3, "WRONG_OVERSTATED"),
        ("UNDERSTATE", -1, "WRONG_UNDERSTATED"),
    ]

    failures, total, results = 0, 0, []
    for fen, name, true_n, mv in cases:
        for tag, delta, want in expectations:
            claimed = true_n + delta
            if claimed < 1:
                continue
            row = {
                "id": f"{name}-{tag}", "fen": fen, "score_value": claimed,
                "bestmove": mv, "pv_len": 0,
                "pv_len_wanted": 2 * claimed - 1, "pv_len_filter_pass": True,
                "engine_sha256": "synthetic", "base_commit": "synthetic",
                "options": {}, "depth": 0,
            }
            v = verify.verify_row(row)
            got = v["class"]
            ok = (got == want)
            total += 1
            failures += 0 if ok else 1
            results.append({"case": row["id"], "claimed": claimed, "true": true_n,
                            "expected": want, "got": got, "pass": ok,
                            "reason": v.get("reason")})
            print(f"  {row['id']:24} claim={claimed:2} true={true_n:2} "
                  f"expect={want:17} got={got:17} {'PASS' if ok else 'FAIL'}")

    print()
    if failures == 0:
        print(f"END-TO-END VALID: {total}/{total} synthetic labels classified correctly")
        print("  honest -> EXACT; over -> WRONG_OVERSTATED; under -> WRONG_UNDERSTATED")
    else:
        print(f"END-TO-END INVALID: {failures}/{total} misclassified")

    with open(paths.work_file("e2e_labels.json"), "w") as f:
        json.dump({"rows": results, "failures": failures, "total": total,
                   "valid": failures == 0}, f, indent=1)
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
