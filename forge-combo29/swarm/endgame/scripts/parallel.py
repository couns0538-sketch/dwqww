#!/usr/bin/env python3
"""Parallel runner: one process per (family, arm, go, net) cell, N workers.

Each worker plays a contiguous slice of the fixture list and writes JSONL, so a
crash or a timeout loses one slice and not the run. Every search has a hard wall
clock; a search that exceeds it is recorded as `search_timeout` rather than being
allowed to stall the whole experiment -- and the count of those is reported, because
a timeout on a three-piece board is itself a result.

Nothing here re-orders or filters the fixtures: the denominator is whatever the
fixture file says, and the slice boundaries are logged.
"""
from __future__ import annotations

import argparse
import json
import multiprocessing as mp
import os
import sys
import time
import traceback

sys.path.insert(0, "/tmp/fx")
import chess
import game
import solver

FIX = "/tmp/fx/fixtures.json"
TABLES = "/tmp/fx/tables.json"
KPKT = "/tmp/fx/kpk_table.json"

_TAB = {}


def load_table(label, path, syms):
    blob = json.load(open(path))
    d = blob[label] if label in blob else blob
    tab = {"syms": syms, "value": {}, "dtm": {}}
    for ks, v in d["value"].items():
        key = json.loads(ks)
        tab["value"][(tuple((int(sq), sym) for sq, sym in key[0]), key[1])] = v
    for ks, v in d["dtm"].items():
        key = json.loads(ks)
        tab["dtm"][(tuple((int(sq), sym) for sq, sym in key[0]), key[1])] = v
    return tab


def table_for(label):
    if label in _TAB:
        return _TAB[label]
    if label in ("KQK", "KRK", "KBK", "KNK"):
        _TAB[label] = load_table(label, TABLES, solver.ALL_SYMS)
    elif label == "KPK":
        _TAB[label] = load_table("KPK", KPKT, solver.PAWN_SYMS)
    else:
        _TAB[label] = None
    return _TAB[label]


def items_for(family, fixture_override=None):
    """The item list for a family.

    `fixture_override` lets a family use a SAMPLE file (the KPK boundary is 81,664
    cells; the sweep plays a stratified sample and must say so). Without it the
    family's own list is used, so the small families are always complete.
    """
    if fixture_override:
        blob = json.load(open(fixture_override))
        return blob["cells"] if "cells" in blob else blob["positions"]
    fx = json.load(open(FIX))
    fam = fx["families"][family]
    return fam["positions"] if "positions" in fam else fam["cells"]


def worker(args):
    (family, arm, go, exe, net, slice_id, lo, hi, outdir, search_timeout,
     fixture_override) = args
    items = items_for(family, fixture_override)
    items = items[lo:hi]
    options = {}
    if net:
        options["NNUEArchFile"] = net
        options["NNUEArch"] = "true"
    path = os.path.join(outdir, f"{slice_id}.jsonl")
    done = 0
    with open(path, "w") as fh:
        for i, p in enumerate(items):
            t0 = time.time()
            try:
                r = game.play(p["fen"], go, arm, table=table_for(family),
                              exe=exe, options=options,
                              max_plies=game.MAX_PLIES,
                              search_timeout=search_timeout or None)
                r["error"] = None
            except Exception as exc:
                r = {"start_fen": p["fen"], "result": "error", "term": "exception",
                     "error": f"{type(exc).__name__}: {exc}",
                     "trace": traceback.format_exc()[-800:],
                     "moves": [], "n_plies": 0, "n_bails": 0, "bails": []}
            r["seconds"] = round(time.time() - t0, 3)
            r["family"] = family
            r["arm"] = arm
            r["go"] = go
            r["net"] = net or "builtin"
            r["slice"] = slice_id
            r["index"] = lo + i
            r["expected"] = p.get("theoretical",
                                  "draw" if family in ("KBK", "KNK") else "win")
            r["dtm_plies_start"] = p.get("dtm_plies")
            r["dtm_moves_start"] = p.get("dtm_moves")
            fh.write(json.dumps(r) + "\n")
            fh.flush()
            done += 1
    return {"slice": slice_id, "family": family, "arm": arm, "go": go,
            "net": net or "builtin", "lo": lo, "hi": hi, "n": done, "path": path}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--family", required=True)
    ap.add_argument("--go", required=True)
    ap.add_argument("--arm", required=True)
    ap.add_argument("--exe", default="/tmp/fx/build/forge")
    ap.add_argument("--net", default=None)
    ap.add_argument("--n", type=int, default=None, help="cap the number of items")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--outdir", required=True)
    ap.add_argument("--search-timeout", type=int, default=0,
                    help="per-search wall clock in seconds; 0 = unbounded")
    ap.add_argument("--order", default="fixture", choices=["fixture"],
                    help="fixtures are used in file order; slicing is contiguous")
    ap.add_argument("--fixtures", default=None,
                    help="override the fixture file for this family (samples)")
    a = ap.parse_args()

    items = items_for(a.family, a.fixtures)
    n = len(items) if a.n is None else min(a.n, len(items))
    os.makedirs(a.outdir, exist_ok=True)

    # Contiguous slices, not striding: a fixture list sorted by FEN would put all
    # of one colour/complex into one stride, and a per-slice failure would then be
    # a systematic bias rather than a random one.
    per = (n + a.workers - 1) // a.workers
    jobs = []
    for s in range(a.workers):
        lo = s * per
        hi = min(n, lo + per)
        if lo >= hi:
            continue
        jobs.append((a.family, a.arm, a.go, a.exe, a.net, f"s{s:02d}", lo, hi,
                     a.outdir, a.search_timeout, a.fixtures))

    t0 = time.time()
    print(f"{a.family} {a.arm} {a.go} net={a.net or 'builtin'} n={n} "
          f"workers={len(jobs)} slices of {per}", flush=True)
    with mp.Pool(len(jobs)) as pool:
        for res in pool.imap_unordered(worker, jobs):
            print(f"  slice {res['slice']} [{res['lo']}:{res['hi']}] done "
                  f"{res['n']} in {time.time()-t0:.0f}s", flush=True)
    print(f"all slices done in {time.time()-t0:.0f}s", flush=True)
    json.dump({"family": a.family, "arm": a.arm, "go": a.go,
               "net": a.net or "builtin", "n": n, "outdir": a.outdir,
               "seconds": round(time.time() - t0, 1),
               "slices": jobs and [{"lo": j[6], "hi": j[7]} for j in jobs]},
              open(os.path.join(a.outdir, "_run.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
