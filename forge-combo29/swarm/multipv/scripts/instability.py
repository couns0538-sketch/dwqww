#!/usr/bin/env python3
"""The control that decides how to read Property 5's difference count.

Question: when MultiPV>1 returns a different move from MultiPV 1, is MultiPV *adding* instability,
or is it exposing a position the search has not settled?

Control: the SAME comparison at MultiPV 1 alone, between two depths.  If the single-PV answer moves
between depth D and depth D+4 at a similar rate, then the MultiPV difference is a display setting
surfacing ordinary depth instability, not a defect.  If the MultiPV rate is materially higher, the
setting is doing something of its own.

Three arms on the same positions:
  A  MultiPV 1 at depth D           (baseline answer)
  B  MultiPV K at depth D           (the arm a GUI user actually sees)
  C  MultiPV 1 at depth D+delta     (a deeper search, i.e. "what more thinking would have said")

Reported as 2x2 agreement over A/B/C, so the difference attributable to the setting (A vs B) can be
read next to the difference attributable to more search (A vs C).

Usage: python3 instability.py <exe> [--positions N] [--depth D] [--delta 4] [--mpv 6]
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import chess

from audit import Tally, load_corpus, search
from multipv_lib import bestmove_of, depth_lines, final_depth_group, score_cp, write_json


def answer(exe, fen, mpv, depth):
    lines = search(exe, fen, mpv, "go depth %d" % depth)
    top, grp = final_depth_group(depth_lines(lines))
    if not grp:
        return None, None, None
    top_line = next((p for p in grp if p["multipv"] == 1), grp[0])
    return (bestmove_of(lines), score_cp(top_line["score_kind"], top_line["score"]),
            [len(p["pv"]) for p in grp])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("exe", nargs="?", default="build/forge")
    ap.add_argument("--positions", type=int, default=40)
    ap.add_argument("--depth", type=int, default=12)
    ap.add_argument("--delta", type=int, default=4)
    ap.add_argument("--mpv", type=int, default=6)
    ap.add_argument("--json")
    args = ap.parse_args()

    t = Tally()
    rows = []
    fens, corpus = load_corpus(args.positions)
    deep = args.depth + args.delta
    for fen in fens:
        a_move, a_score, _ = answer(args.exe, fen, 1, args.depth)
        b_move, b_score, _ = answer(args.exe, fen, args.mpv, args.depth)
        c_move, c_score, _ = answer(args.exe, fen, 1, deep)
        if None in (a_move, b_move, c_move):
            t.add("skipped")
            continue
        t.add("positions")
        rows.append({"fen": fen, "a_move": a_move, "b_move": b_move, "c_move": c_move,
                     "a_score": a_score, "b_score": b_score, "c_score": c_score,
                     "setting_changed": a_move != b_move, "depth_changed": a_move != c_move,
                     "b_matches_c": b_move == c_move})
        if a_move != b_move:
            t.add("A_ne_B_setting_changed_move")
        if a_move != c_move:
            t.add("A_ne_C_deeper_changed_move")
        if b_move != c_move:
            t.add("B_ne_C")
        if a_move == b_move == c_move:
            t.add("all_three_agree")
        if a_move != b_move and a_move == c_move:
            t.add("setting_changed_but_deeper_confirms_multipv1")
        if a_move != b_move and b_move == c_move:
            t.add("setting_changed_and_deeper_confirms_multipv")
        if a_move != c_move and a_move == b_move:
            t.add("deeper_changed_but_multipv_kept_multipv1_answer")
        if a_move != b_move and a_move != c_move and b_move != c_move:
            t.add("three_distinct_moves")
        if a_score is not None and b_score is not None:
            t.add("score_gap_bucket:" + ("0" if a_score == b_score else
                                         "1-19" if abs(b_score - a_score) <= 19 else
                                         "20-49" if abs(b_score - a_score) <= 49 else "50+"))

    print(json.dumps(t.as_dict(), indent=1))
    if args.json:
        write_json(args.json, {"tally": t.as_dict(), "rows": rows, "corpus": corpus,
                       "depth": args.depth, "deep_depth": deep, "mpv": args.mpv})
        print("wrote", args.json)
    return 0


if __name__ == "__main__":
    sys.exit(main())
