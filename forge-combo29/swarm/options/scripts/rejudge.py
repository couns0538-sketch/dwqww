#!/usr/bin/env python3
"""Re-adjudicate stored arm results with the current mate predicate.

The audit first ran with a mate checker that compared PV LENGTH to the claimed
distance. That was wrong — the PV cannot exceed the search depth, so on a long
mate it is necessarily shorter — and it flagged real mates as false. The rows it
produced are still in the JSON, with the fields needed to judge them properly.

This script takes those stored rows and re-decides each mate claim with the
sound predicate: prove the position reached by the engine's OWN bestmove, for the
side that should now be mating, and compare with the claim. No engine run is
needed, because (fen, mate, bestmove) is everything the question depends on.

It rewrites the mate section of each arm in place, and prints a before/after
count so the size of the correction is visible rather than implied.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

import chess

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import audit  # noqa: E402


def rejudge(arm: dict) -> tuple[dict, int, int]:
    """Recompute one arm's mate section. Returns (section, was, now)."""
    m = arm["mates"]
    rows = []
    unsound = []
    imprecise = []
    missed = []
    unproved = []
    for row in m["rows"]:
        board = chess.Board(row["fen"])
        new = dict(row)
        new.pop("pv_problem", None)
        new.pop("pv_confirms_mate", None)
        new.pop("unsound_reason", None)
        if row.get("mate") is not None:
            verdict = audit.mate_verdict(board, row["mate"], row["bestmove"])
            new.update({k: v for k, v in verdict.items() if k != "verdict"})
            new["claim_verdict"] = verdict["verdict"]
            if verdict["verdict"] == "FALSE":
                new["verdict"] = "UNSOUND"
                unsound.append(new)
            elif verdict["verdict"] == "UNPROVED":
                new["verdict"] = "UNPROVED"
                unproved.append(new)
            else:
                new["verdict"] = "ok"
                if new.get("proved_plies", row["proved_plies"]) > row["proved_plies"]:
                    imprecise.append(new)
        else:
            new["verdict"] = "MISSED"
            missed.append(new)
        rows.append(new)

    section = {
        "fixtures": m["fixtures"],
        "unsound": len(unsound),
        "unsound_rows": unsound,
        "regressions_vs_baseline": m.get("regressions_vs_baseline", 0),
        "regression_rows": m.get("regression_rows", []),
        "missed": len(missed),
        "missed_rows": missed,
        "imprecise": len(imprecise),
        "unproved": len(unproved),
        "unproved_rows": unproved,
        "claimed_mates": sum(1 for r in rows if r.get("mate") is not None),
        "claims_proved": sum(1 for r in rows if r.get("claim_verdict") in
                             ("TRUE_EXACT", "TRUE_FAST", "TRUE_LONG")),
        "rows": rows,
        "predicate": "prove-after-bestmove v2",
    }
    return section, m.get("unsound", 0), len(unsound)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--audit", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    arms = json.load(open(args.audit))
    total_before = total_after = 0
    for name, arm in arms.items():
        if arm.get("error") or "mates" not in arm:
            continue
        section, before, after = rejudge(arm)
        arm["mates"] = section
        total_before += before
        total_after += after
        print(f"{name:24s} unsound {before} -> {after}   "
              f"proved {section['claims_proved']}/{section['claimed_mates']}", flush=True)

    with open(args.out, "w") as fh:
        json.dump(arms, fh)
    print(f"\nTOTAL unsound {total_before} -> {total_after}")
    if total_after:
        print("There are still FALSE claims. Those are real and must be read case by case.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
