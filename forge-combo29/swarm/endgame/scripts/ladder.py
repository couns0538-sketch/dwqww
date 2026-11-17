#!/usr/bin/env python3
"""Depth ladder on the CONVERSION FAILURES.

The question the coordinator named: if a won ending does not convert, is that a
horizon effect (deeper search fixes it) or a defect that survives depth? A failure at
depth 12 that converts at depth 16 is a horizon effect and is a much weaker claim.

The ladder is run on the positions that FAILED at the base budget, so it answers the
right question -- "does depth rescue this exact position" -- rather than on a fresh
sample. The FENs come from the recorded JSONL, so the ladder cannot drift onto a
different position set.

Also recorded per rung: the score at the first ply, because "the engine did not know
it was winning" and "the engine knew and shuffled anyway" are different defects.
"""
from __future__ import annotations

import argparse
import glob
import json
import multiprocessing as mp
import os
import sys

sys.path.insert(0, "/tmp/fx")
import game
import parallel


def failed_fens(prod_glob):
    out = []
    for d in sorted(glob.glob(prod_glob)):
        for f in glob.glob(os.path.join(d, "*.jsonl")):
            for line in open(f):
                r = json.loads(line)
                if r["result"] not in ("converted", "converted_after_timeout") and \
                        r.get("expected") == "win":
                    out.append({"fen": r["start_fen"], "family": r["family"],
                                "failed_at": r["go"], "result": r["result"],
                                "term": r["term"], "n_plies": r["n_plies"],
                                "dtm_moves_start": r.get("dtm_moves_start")})
    # de-duplicate on (fen, family, budget) so two budgets failing one FEN stay apart
    seen, uniq = set(), []
    for x in out:
        k = (x["fen"], x["family"], x["failed_at"])
        if k in seen:
            continue
        seen.add(k)
        uniq.append(x)
    return uniq


def work(args):
    item, go, arm, timeout, fam = args
    r = game.play(item["fen"], go, arm, table=parallel.table_for(fam),
                  search_timeout=timeout)
    first = next((p for p in r["plies"] if p["source"] == "engine"), {})
    return {"fen": item["fen"], "family": fam, "arm": arm, "go": go,
            "failed_at": item["failed_at"],
            "result": r["result"], "term": r["term"], "n_plies": r["n_plies"],
            "moves": (r["n_plies"] + 1) // 2,
            "first_score": first.get("score"), "first_kind": first.get("score_kind"),
            "bails": r["n_bails"], "timeouts": r["n_search_timeouts"],
            "dtm_moves_start": item.get("dtm_moves_start"),
            "sans": r["sans"]}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--glob", default="/tmp/fx/prod/KQK_engine*")
    ap.add_argument("--depths", default="8,12,16,20")
    ap.add_argument("--arm", default="engine")
    ap.add_argument("--timeout", type=int, default=40)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    fails = failed_fens(a.glob)
    print(f"{len(fails)} failed positions from {a.glob}", flush=True)
    jobs = []
    for d in a.depths.split(","):
        for it in fails:
            jobs.append((it, f"go depth {d.strip()}", a.arm, a.timeout, it["family"]))
    rows = []
    with mp.Pool(a.workers) as pool:
        for r in pool.imap_unordered(work, jobs):
            rows.append(r)
            print(f"  d={r['go'].split()[-1]:>2} {r['family']:5s} {r['result']:10s} "
                  f"{r['term']:18s} moves={r['moves']:3d} first={r['first_kind']} "
                  f"{r['first_score']} {r['fen']}", flush=True)
    json.dump(rows, open(a.out, "w"), indent=1)
    print("wrote", a.out)
