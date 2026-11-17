#!/usr/bin/env python3
"""One question, measured directly: does ANY emitted line have len(pv) > seldepth?

This exists because a report sentence compared two different quantities and became unquotable.
The two arms were:

  MultiPV>1   `check_pv_vs_seldepth(block)` -> the length of the list of lines VIOLATING
              `len(pv) > seldepth`.  0 means no violation.
  MultiPV 1   a counter that incremented `pv_len_le_seldepth` when
              `len(pv) <= seldepth`, else `pv_len_gt_seldepth`.  480 means 480 blocks SATISFIED
              the predicate.

So "0 at MultiPV>1, 480 of 480 at MultiPV 1" was a violation count beside a clean count.  Rather
than reword it on trust, this script re-derives both from the wire and reports, per line:

  lines_total          every `info depth` line emitted
  violation_count      lines with len(pv) > seldepth
  clean_count          lines with len(pv) <= seldepth
  missing_seldepth     lines with no seldepth field at all (neither clean nor violating)
  worst_margin         max over lines of (len(pv) - seldepth); <= 0 means no line violates
  max_pv_minus_depth   the same against `depth`, which DOES go positive

It also prints the per-MultiPV breakdown, so "at MultiPV>1" is enumerated rather than a range
the reader has to interpret.

Usage: python3 seldepth_check.py <exe> [--positions N] [--depth 12] [--json out.json]
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from audit import load_corpus, search
from multipv_lib import depth_lines, write_json

MPVS = (1, 2, 3, 4, 6)


def measure(exe, fens, mpv, depth):
    """Every line at every depth of every position, reduced to counters."""
    r = {"mpv": mpv, "positions": len(fens), "lines_total": 0, "blocks_total": 0,
         "violation_count": 0, "clean_count": 0, "missing_seldepth": 0,
         "worst_pv_minus_seldepth": None, "max_pv_minus_depth": None,
         "lines_with_pv_longer_than_depth": 0, "examples": []}
    for fen in fens:
        for info in depth_lines(search(exe, fen, mpv, "go depth %d" % depth)):
            r["lines_total"] += 1
            n, sd, d = len(info["pv"]), info["seldepth"], info["depth"]
            if sd is None:
                r["missing_seldepth"] += 1
            else:
                margin = n - sd
                if r["worst_pv_minus_seldepth"] is None or margin > r["worst_pv_minus_seldepth"]:
                    r["worst_pv_minus_seldepth"] = margin
                if margin > 0:
                    r["violation_count"] += 1
                    if len(r["examples"]) < 10:
                        r["examples"].append({"fen": fen, "multipv": info["multipv"],
                                              "depth": d, "seldepth": sd, "pv_len": n})
                else:
                    r["clean_count"] += 1
            dm = n - d
            if r["max_pv_minus_depth"] is None or dm > r["max_pv_minus_depth"]:
                r["max_pv_minus_depth"] = dm
            if dm > 0:
                r["lines_with_pv_longer_than_depth"] += 1
        # count blocks as distinct (position, depth) pairs
        r["blocks_total"] += len({i["depth"] for i in depth_lines(
            search(exe, fen, mpv, "go depth %d" % depth))})
    return r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("exe", nargs="?", default="build/forge")
    ap.add_argument("--positions", type=int, default=40)
    ap.add_argument("--depth", type=int, default=12)
    ap.add_argument("--json")
    args = ap.parse_args()

    fens, corpus = load_corpus(args.positions)
    arms = [measure(args.exe, fens, mpv, args.depth) for mpv in MPVS]

    gt1 = [a for a in arms if a["mpv"] > 1]
    agg = {
        "predicate": "len(pv) > seldepth",
        "depth": args.depth,
        "positions": len(fens),
        "corpus": corpus,
        "per_mpv": arms,
        "multipv_gt1_mpvs": [a["mpv"] for a in gt1],
        "multipv_gt1_lines_total": sum(a["lines_total"] for a in gt1),
        "multipv_gt1_violations": sum(a["violation_count"] for a in gt1),
        "multipv_gt1_clean": sum(a["clean_count"] for a in gt1),
        "multipv_gt1_missing_seldepth": sum(a["missing_seldepth"] for a in gt1),
        "multipv1_lines_total": arms[0]["lines_total"],
        "multipv1_violations": arms[0]["violation_count"],
        "multipv1_clean": arms[0]["clean_count"],
        "multipv1_missing_seldepth": arms[0]["missing_seldepth"],
        "all_lines_total": sum(a["lines_total"] for a in arms),
        "all_violations": sum(a["violation_count"] for a in arms),
        "any_line_violates": any(a["violation_count"] > 0 for a in arms),
        # contrast: the SAME measurement against `depth` instead of seldepth
        "all_lines_pv_longer_than_depth": sum(a["lines_with_pv_longer_than_depth"] for a in arms),
        # a scalar so the report can cite it: the largest len(pv)-seldepth anywhere in the corpus
        "worst_margin": max(a["worst_pv_minus_seldepth"] for a in arms),
        "per_mpv_worst": {a["mpv"]: a["worst_pv_minus_seldepth"] for a in arms},
        "per_mpv_violations": {a["mpv"]: a["violation_count"] for a in arms},
    }
    print(json.dumps({k: v for k, v in agg.items() if k not in ("per_mpv", "corpus")}, indent=1))
    print("per-MPV violation counts:", {a["mpv"]: a["violation_count"] for a in arms})
    print("per-MPV worst (len(pv) - seldepth):",
          {a["mpv"]: a["worst_pv_minus_seldepth"] for a in arms})
    if args.json:
        print("wrote", write_json(args.json, agg))
    return 0


if __name__ == "__main__":
    sys.exit(main())
