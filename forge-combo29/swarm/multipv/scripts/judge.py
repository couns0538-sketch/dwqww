#!/usr/bin/env python3
"""Property 5's judge: does a DEEPER full-width search back the move MultiPV>1 printed?

The naive judge is a `searchmoves <move>` re-search.  It is not neutral: restricting the root
changes the aspiration sequence and the TT context, and its noise floor on the same move at the
same depth is measured in agreement.py (12/12 pairs disagree by 0-30 cp).  A judge that noisy
cannot adjudicate a 20-40 cp difference, so this script uses a different one.

Judge: a full-width MultiPV 1 search, four plies deeper, on the same position.  Three outcomes:

  printed_confirmed    deeper search plays the move MultiPV>1 printed
  single_pv_confirmed  deeper search plays the move MultiPV 1 gave
  third_move           deeper search plays neither — the position is not settled at this depth

The `third_move` arm is the one that decides how to read the other two.  If the deeper search keeps
inventing new moves, then a MultiPV-vs-MultiPV-1 move difference is evidence that the position is
unsettled, not that the setting is wrong.  That is why the SAME classification is also run for the
MultiPV 1 answer alone between depth D and D+4 — the no-setting control.

Usage: python3 judge.py <exe> [--positions N] [--depth D] [--judge-depth J] [--mpv K]
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import chess

from audit import Tally, load_corpus, search
from multipv_lib import bestmove_of, depth_lines, final_depth_group, score_cp


def answer(exe, fen, mpv, depth):
    lines = search(exe, fen, mpv, "go depth %d" % depth)
    top, grp = final_depth_group(depth_lines(lines))
    if not grp or not grp[0]["pv"]:
        return None, None
    one = next((p for p in grp if p["multipv"] == 1), grp[0])
    return bestmove_of(lines), score_cp(one["score_kind"], one["score"])


def classify(printed, single, deep):
    if deep == printed:
        return "printed_confirmed"
    if deep == single:
        return "single_pv_confirmed"
    return "third_move"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("exe", nargs="?", default="build/forge")
    ap.add_argument("--positions", type=int, default=40)
    ap.add_argument("--depth", type=int, default=12)
    ap.add_argument("--judge-depth", type=int, default=16)
    ap.add_argument("--mpv", type=int, default=6)
    ap.add_argument("--json")
    args = ap.parse_args()

    t = Tally()
    rows = []
    fens, corpus = load_corpus(args.positions)
    for fen in fens:
        t.add("positions")
        single, s_score = answer(args.exe, fen, 1, args.depth)
        printed, p_score = answer(args.exe, fen, args.mpv, args.depth)
        if single is None or printed is None:
            t.add("skipped")
            continue
        deep, d_score = answer(args.exe, fen, 1, args.judge_depth)
        # The no-setting control: the MultiPV 1 answer between depth D and the judge depth.
        # Same two candidates, same comparator, no MultiPV involved at either end.
        control_verdict = "multipv1_stable" if deep == single else "multipv1_moved"

        row = {"fen": fen, "single_pv": single, "printed": printed,
               "deep": deep, "judge_depth": args.judge_depth,
               "scores": {"single_pv": s_score, "printed": p_score, "deep": d_score}}
        if single == printed:
            t.add("same_move")
            t.add("control_" + control_verdict)
            row["verdict"] = "same"
            rows.append(row)
            continue
        t.add("move_changed")
        verdict = classify(printed, single, deep)
        row["verdict"] = verdict
        t.add(verdict)
        t.add("control_" + control_verdict)
        # how much the printed score was off, against the deeper search of that same position
        if p_score is not None and d_score is not None:
            row["printed_minus_deep"] = p_score - d_score
        rows.append(row)

    # the two populations, counted by size rather than by one increment per row
    unchanged = [r for r in rows if r["verdict"] == "same"]
    changed = [r for r in rows if r["verdict"] != "same"]
    t.d["unchanged_positions"] = len(unchanged)
    t.d["changed_positions"] = len(changed)
    t.d["unchanged_depth_moved_count"] = sum(1 for r in unchanged if r["deep"] != r["single_pv"])
    t.d["changed_depth_moved_count"] = sum(1 for r in changed if r["deep"] != r["single_pv"])
    t.d["changed_printed_confirmed_count"] = sum(
        1 for r in changed if r["verdict"] == "printed_confirmed")
    t.d["changed_single_confirmed_count"] = sum(
        1 for r in changed if r["verdict"] == "single_pv_confirmed")
    t.d["changed_third_move_count"] = sum(1 for r in changed if r["verdict"] == "third_move")
    # rate of "a deeper search changed the move" with and without the setting in play
    t.d["control_depth_moved_rate_pct"] = round(
        100.0 * t.d["control_multipv1_moved"] / max(1, t.get("positions")), 1)
    t.d["setting_changed_rate_pct"] = round(
        100.0 * t.get("move_changed") / max(1, t.get("positions")), 1)

    print(json.dumps(t.as_dict(), indent=1))
    if args.json:
        with open(args.json, "w") as fh:
            json.dump({"tally": t.as_dict(), "rows": rows, "corpus": corpus,
                       "depth": args.depth, "judge_depth": args.judge_depth,
                       "mpv": args.mpv}, fh, indent=1)
        print("wrote", args.json)
    return 0


if __name__ == "__main__":
    sys.exit(main())
