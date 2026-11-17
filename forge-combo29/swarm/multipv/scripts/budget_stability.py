#!/usr/bin/env python3
"""How stable is the short-final-block count under a budget? Measured, three repeats each.

The first draft of this report quoted a single pass (28 of 40 short).  A later pass on the same
binary and corpus gave 32 of 40.  Neither is wrong and neither is reportable on its own: `go movetime`
stops at a wall-clock instant, so which line an iteration dies on depends on machine load.  A count
that moves between runs must be stated as a range with its repeats, or it is the "two counts side by
side with no explanation" failure in reverse — one count, presented as if it were stable.

This script runs the same measurement three times per budget kind and reports every repeat, so the
number in the report can be a range with its evidence rather than one sample dressed as a fact.

Usage: python3 budget_stability.py <exe> [--positions N] [--mpv 6] [--repeats 3]
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import chess

from audit import load_corpus, search
from multipv_lib import bestmove_of, depth_lines, final_depth_group

BUDGETS = ["go movetime 200", "go nodes 20000"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("exe", nargs="?", default="build/forge")
    ap.add_argument("--positions", type=int, default=20)
    ap.add_argument("--mpv", type=int, default=6)
    ap.add_argument("--repeats", type=int, default=3)
    ap.add_argument("--json")
    args = ap.parse_args()

    fens, corpus = load_corpus(args.positions)
    out = {"corpus": corpus, "positions": len(fens), "mpv": args.mpv,
           "repeats": args.repeats, "budgets": {}}

    for go in BUDGETS:
        per_repeat = []
        for _ in range(args.repeats):
            short = full = bestmove_bad = identical_reply = 0
            sizes = {}
            for fen in fens:
                lines = search(args.exe, fen, args.mpv, go)
                infos = depth_lines(lines)
                top, final = final_depth_group(infos)
                expected = min(args.mpv, chess.Board(fen).legal_moves.count())
                if len(final) != expected:
                    short += 1
                    sizes[str(min(len(final), args.mpv))] = sizes.get(str(min(len(final), args.mpv)), 0) + 1
                else:
                    full += 1
                    sizes[str(expected)] = sizes.get(str(expected), 0) + 1
                one = next((p for p in final if p["multipv"] == 1), None)
                if one is None or not one["pv"] or one["pv"][0] != bestmove_of(lines):
                    bestmove_bad += 1
            per_repeat.append({"short": short, "full": full,
                               "bestmove_disagrees": bestmove_bad,
                               "final_line_count_histogram": dict(sorted(sizes.items()))})
        shorts = [r["short"] for r in per_repeat]
        out["budgets"][go] = {
            "repeats": per_repeat,
            "short_min": min(shorts), "short_max": max(shorts),
            "stable": len(set(shorts)) == 1,
            "bestmove_all_agree": all(r["bestmove_disagrees"] == 0 for r in per_repeat),
        }
        print("%-22s short-final per repeat %s   stable=%s   bestmove always agrees=%s"
              % (go, shorts, out["budgets"][go]["stable"],
                 out["budgets"][go]["bestmove_all_agree"]))

    if args.json:
        with open(args.json, "w") as fh:
            json.dump(out, fh, indent=1)
        print("wrote", args.json)
    return 0


if __name__ == "__main__":
    sys.exit(main())
