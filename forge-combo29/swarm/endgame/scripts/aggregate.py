#!/usr/bin/env python3
"""Aggregate every production directory into one numbers file.

Reports, per (family, arm, go, net):
  conversion rate with its denominator -- never a bare percentage
  the ply distribution: min / median / max, and the move count (plies+1)//2
  bails, search timeouts, and games that ended by the fifty-move rule
  for KPK: the cells where the result disagreed with the exact table, listed
Everything is computed from the JSONL files, so the number in FINDINGS.md can be
re-derived from the artefacts rather than retyped.
"""
from __future__ import annotations

import glob
import json
import os
import statistics
import sys
from collections import Counter, defaultdict

PROD = sys.argv[1] if len(sys.argv) > 1 else "/tmp/fx/prod"
OUT = sys.argv[2] if len(sys.argv) > 2 else "/tmp/fx/numbers.json"


def load_dir(d):
    rows = []
    for f in sorted(glob.glob(os.path.join(d, "*.jsonl"))):
        for line in open(f):
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def summarise(rows):
    n = len(rows)
    c = Counter(r["result"] for r in rows)
    plies = sorted(r["n_plies"] for r in rows)
    moves = sorted((r["n_plies"] + 1) // 2 for r in rows)
    terms = Counter(r["term"] for r in rows)
    bails = sum(r.get("n_bails", 0) for r in rows)
    return {
        "n": n,
        "converted": c["converted"] + c["converted_after_timeout"],
        "converted_clean": c["converted"],
        "converted_after_timeout": c["converted_after_timeout"],
        "drawn": c["drawn"],
        "lost": c["lost"],
        "unfinished": c["unfinished"],
        "error": c["error"],
        "conversion_rate": round((c["converted"] + c["converted_after_timeout"]) / n, 4) if n else None,
        "plies_min": plies[0] if plies else None,
        "plies_median": statistics.median(plies) if plies else None,
        "plies_max": plies[-1] if plies else None,
        "moves_min": moves[0] if moves else None,
        "moves_median": statistics.median(moves) if moves else None,
        "moves_max": moves[-1] if moves else None,
        "terms": dict(terms),
        "bails": bails,
        "games_with_bail": sum(1 for r in rows if r.get("n_bails")),
        "search_timeouts": sum(r.get("n_search_timeouts", 0) for r in rows),
        "games_with_timeout": sum(1 for r in rows if r.get("n_search_timeouts")),
        "fifty_move_draws": terms.get("fifty_move_claim", 0),
        "seconds": round(sum(r.get("seconds", 0) for r in rows), 1),
        "go": rows[0].get("go") if rows else None,
        "net": rows[0].get("net") if rows else None,
        "arm": rows[0].get("arm") if rows else None,
    }


def failures(rows):
    out = []
    for r in rows:
        if r["result"] in ("drawn", "lost", "unfinished", "error") and r.get("expected") == "win":
            out.append({"fen": r["start_fen"], "result": r["result"],
                        "term": r["term"], "n_plies": r["n_plies"],
                        "dtm_moves_start": r.get("dtm_moves_start"),
                        "bails": r.get("n_bails"),
                        "fifty": r["term"] == "fifty_move_claim",
                        "sans": r.get("sans"),
                        "moves": r.get("moves")})
    return out


def main():
    dirs = sorted(d for d in glob.glob(os.path.join(PROD, "*")) if os.path.isdir(d))
    numbers = {"cells": {}, "generated_from": PROD}
    for d in dirs:
        rows = load_dir(d)
        if not rows:
            continue
        key = os.path.basename(d)
        s = summarise(rows)
        f = failures(rows)
        s["failures"] = f
        s["n_failures"] = len(f)
        numbers["cells"][key] = s
        print(f"{key:46s} n={s['n']:4d} conv={s['converted']:4d}/{s['n']:<4d} "
              f"({(s['conversion_rate'] or 0)*100:5.1f}%) drawn={s['drawn']:3d} "
              f"lost={s['lost']:3d} unf={s['unfinished']:2d} err={s['error']:2d} "
              f"moves {s['moves_min']}-{s['moves_max']} med={s['moves_median']} "
              f"bails={s['bails']} t/o={s['search_timeouts']} 50mv={s['fifty_move_draws']}")
    json.dump(numbers, open(OUT, "w"), indent=1)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
