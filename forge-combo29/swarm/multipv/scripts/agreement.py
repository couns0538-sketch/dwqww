#!/usr/bin/env python3
"""Property 5, with a real judge: when MultiPV>1 prints a DIFFERENT multipv-1 line, is it better?

A GUI user sees the arrow move when they change the MultiPV spinner from 1 to N.  Two things can
produce that, and they need different advice:

  (a) PROMOTION — an excluded-root alternate really is better at this depth;
  (b) SELECTION — the alternate outscores the primary only because it was searched in a different
      context (its own table, cleared per line, no aspiration history), and a wider search does not
      confirm it.

The judge is a DEEPER FULL-WIDTH search at MultiPV 1, not a `searchmoves` re-search.  A
single-move-restricted search at the same depth is not a neutral referee: it changes the root's
aspiration and its TT context, so it disagrees with its own full-width twin — that is measured
here as the noise floor and reported, so nobody reads it as a verdict.

Reported per position where the move changed:
  - which move the deeper search prefers: the printed one or the single-PV one
  - the deeper search's score for each of the two moves (via searchmoves at the deeper depth,
    whose bias is the same for both moves, so the comparison is fair even though each is biased)
  - how far the printed score was from the deeper search's score for that same move

Usage: python3 agreement.py <exe> [--positions N] [--depth D] [--judge-depth J] [--mpv K]
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import chess

from audit import Tally, load_corpus, search
from multipv_lib import bestmove_of, depth_lines, final_depth_group, score_cp, write_json


def final(exe, fen, multipv, go):
    lines = search(exe, fen, multipv, go)
    top, grp = final_depth_group(depth_lines(lines))
    return lines, top, grp


def score_moves_at(exe, fen, moves, depth):
    """Score each move with a restricted search at `depth`. Same restriction for both, so the
    bias is common-mode and the DIFFERENCE is the thing that is read."""
    out = {}
    for mv in moves:
        lines, top, grp = final(exe, fen, 1, "go depth %d searchmoves %s" % (depth, mv))
        out[mv] = None if not grp or not grp[0]["pv"] else score_cp(grp[0]["score_kind"], grp[0]["score"])
    return out


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
        _, _, f1 = final(args.exe, fen, 1, "go depth %d" % args.depth)
        _, topK, fK = final(args.exe, fen, args.mpv, "go depth %d" % args.depth)
        if not f1 or not fK or not f1[0]["pv"]:
            t.add("skipped")
            continue
        one = next((p for p in fK if p["multipv"] == 1), None)
        if one is None or not one["pv"]:
            t.add("skipped_no_multipv1")
            continue
        t.add("positions")
        s_move, p_move = f1[0]["pv"][0], one["pv"][0]
        row = {"fen": fen, "depth": topK,
               "single_pv_move": s_move, "printed_move": p_move,
               "single_pv_score": score_cp(f1[0]["score_kind"], f1[0]["score"]),
               "printed_score": score_cp(one["score_kind"], one["score"]),
               "bestmove": bestmove_of(search(args.exe, fen, args.mpv, "go depth %d" % args.depth))}
        if s_move == p_move:
            t.add("same_move")
            row["verdict"] = "same"
            rows.append(row)
            continue
        t.add("move_changed")

        # judge: a deeper full-width MultiPV 1 search on the same position
        _, tj, fj = final(args.exe, fen, 1, "go depth %d" % args.judge_depth)
        judge_move = fj[0]["pv"][0] if fj and fj[0]["pv"] else None
        row["judge_depth"] = tj
        row["judge_move"] = judge_move
        # and the judge's own scores for the two candidates, same restriction for both
        both = score_moves_at(args.exe, fen, [s_move, p_move], args.judge_depth)
        row["judge_score_single_move"] = both.get(s_move)
        row["judge_score_printed_move"] = both.get(p_move)
        if judge_move == p_move:
            t.add("judge_prefers_PRINTED")
            row["verdict"] = "printed_confirmed"
        elif judge_move == s_move:
            t.add("judge_prefers_single_pv")
            row["verdict"] = "printed_rejected"
        else:
            t.add("judge_prefers_a_third_move")
            row["verdict"] = "third_move"
        if both.get(s_move) is not None and both.get(p_move) is not None:
            d = both[p_move] - both[s_move]
            row["judge_delta_printed_minus_single"] = d
            t.add("judge_delta_positive" if d > 0 else
                  "judge_delta_zero" if d == 0 else "judge_delta_negative")
        # how optimistic was the advertised score, against the deeper search of that move?
        if both.get(p_move) is not None:
            gap = row["printed_score"] - both[p_move]
            row["printed_minus_judge_for_printed_move"] = gap
            a = abs(gap)
            t.add("printed_vs_judge:" + ("0" if a == 0 else "1-9" if a <= 9 else
                                         "10-49" if a <= 49 else "50-199" if a <= 199 else "200+"))
            if gap > 0:
                t.add("printed_optimistic_vs_judge")
            elif gap < 0:
                t.add("printed_pessimistic_vs_judge")
        rows.append(row)

    # noise floor: at the SAME depth, does a single-move-restricted search agree with the full-width
    # one on that same move?  This is the bias the judge comparison inherits, measured.
    nf = Tally()
    for fen in fens:
        _, _, f1 = final(args.exe, fen, 1, "go depth %d" % args.depth)
        if not f1 or not f1[0]["pv"]:
            continue
        mv = f1[0]["pv"][0]
        _, _, fr = final(args.exe, fen, 1, "go depth %d searchmoves %s" % (args.depth, mv))
        if not fr or not fr[0]["pv"]:
            continue
        a = score_cp(f1[0]["score_kind"], f1[0]["score"])
        b = score_cp(fr[0]["score_kind"], fr[0]["score"])
        nf.add("pairs")
        nf.add("agree" if a == b else "differ")
        nf.add(abs(b - a) // 10 * 10)
    noise = {"pairs": nf.get("pairs"), "agree": nf.get("agree"), "differ": nf.get("differ"),
             "abs_gap_histogram_by_10cp": {str(k): v for k, v in nf.as_dict().items()
                                           if isinstance(k, int)}}

    print(json.dumps({"tally": t.as_dict(), "noise_floor": noise}, indent=1))
    if args.json:
        write_json(args.json, {"tally": t.as_dict(), "rows": rows, "corpus": corpus,
                       "noise_floor": noise,
                       "depth": args.depth, "judge_depth": args.judge_depth,
                       "mpv": args.mpv})
        print("wrote", args.json)
    return 0


if __name__ == "__main__":
    sys.exit(main())
