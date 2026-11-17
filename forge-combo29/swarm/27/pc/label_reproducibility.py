#!/usr/bin/env python3
"""label_reproducibility.py <exe> <outdir> [--settings PC20] [--reps 3]

THE question a training-label pipeline cares about, which nothing in my record has answered directly:
take positions from REAL GAMES and the owner's ACTUAL match budgets, run each cell in K fresh processes, and
ask whether the LABEL (bestmove, score, depth, node count) is identical every time.

S-N1 answered this for `softnodes 2000/20000` on four positions; S-C12 showed the nodes differ between
`go nodes` and `go softnodes`; but neither ran the match budgets (20000 / 50000 / 250000) repeatedly on a
broad real-game sample and counted how many cells are reproducible. That count is what decides whether a label
produced this way can be trusted, so it is the measurement below.

Each cell reports the number of DISTINCT (bestmove, score, depth, nodes) tuples over the reps, and the run is
summarised as "reproducible cells / total cells". Any non-reproducible cell is listed with its variants.

Threads 1 (the owner plays one thread), Hash 16, OwnBook false, fresh process per rep.
"""
import argparse
import json
import os
import re
import statistics
import subprocess
import sys
import time

S14 = ["LmrQuietBase 93", "LmrQuietDivisor 205", "LmrNoisyBase 13", "LmrNoisyDivisor 333",
       "LmrHistoryDivisor 5643", "NullMoveBase 5", "LmpBase 8", "HistoryPruneMultiplier 2220",
       "HistoryBonusQuadratic 24", "HistoryBonusLinear 54", "HistoryBonusMax 2212",
       "SingularDepth 6", "IirDepth 2", "NonPawnCorrection true"]
PC20X = ["CuckooRep true", "HistRework 2", "TtPruneV2 true", "CorrHistV2 true",
         "MateAlphaGuard true", "OwnBook value false" ]

# 8 real-game-family middlegame FENs, drawn from the O/G families other seats use
FENS = [
    "rnb1kbnr/ppp1pppp/8/4q3/8/2N5/PPPP1PPP/R1BQKBNR w KQkq - 2 4",
    "rnbqkbnr/pp2pppp/2p5/8/2pP4/4P3/PP3PPP/RNBQKBNR w KQkq - 0 4",
    "rnbqk1nr/pppp1ppp/3b4/4p3/3PP3/5N2/PPP2PPP/RNBQKB1R b KQkq - 0 3",
    "r1bqk2r/ppp1bppp/3p1n2/8/3QP3/2N5/PPP1BPPP/R1B1K2R w KQkq - 2 8",
    "rnbqkbnr/ppp2ppp/4P3/8/8/8/PPPP1PPP/RNBQKBNR b KQkq - 0 3",
    "r1bqkbnr/ppp1pppp/3p4/3Pn3/4P3/8/PPP2PPP/RNBQKBNR w KQkq - 1 4",
    "rnbqkbnr/p1pp1ppp/1p2p3/8/3PP3/8/PPP2PPP/RNBQKBNR w KQkq - 0 3",
    "r1bqk1nr/pppp1pp1/2n4p/2b5/2BPP3/5N2/PP3PPP/RNBQK2R b KQkq - 0 6",
]
BUDGETS = ["go nodes 20000", "go nodes 50000", "go nodes 250000",
           "go softnodes 20000", "go softnodes 50000", "go softnodes 250000"]


class Missing(Exception):
    pass


def run(exe, settings, fen, limit, timeout=600):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)

    def s(x):
        p.stdin.write(x + "\n"); p.stdin.flush()

    def until(pred, tmo=timeout):
        t0 = time.monotonic(); out = []
        while time.monotonic() - t0 < tmo:
            ln = p.stdout.readline()
            if not ln:
                break
            y = ln.rstrip("\n"); out.append(y)
            if pred(y):
                return out, True
        return out, False

    try:
        s("uci")
        _, ok = until(lambda x: x.strip() == "uciok")
        if not ok:
            raise Missing("no uciok")
        for item in settings:
            name, _, val = item.rpartition(" ")
            s("setoption name %s value %s" % (name, val))
        s("ucinewgame"); s("isready")
        until(lambda x: x.strip() == "readyok")
        s("position fen " + fen); s("isready")
        until(lambda x: x.strip() == "readyok")
        s(limit)
        lines, ok = until(lambda x: x.startswith("bestmove"), tmo=timeout)
        if not ok:
            raise Missing("no bestmove for %r %r" % (fen, limit))
        infos = [l for l in lines if l.startswith("info depth")]
        if not infos:
            raise Missing("no info depth for %r %r" % (fen, limit))
        last = infos[-1]
        d = re.search(r"depth (\d+)", last)
        n = re.search(r"nodes (\d+)", last)
        sc = re.search(r"score (cp|mate) (-?\d+)", last)
        bm = next(l for l in lines if l.startswith("bestmove")).split()[1]
        return {"depth": int(d.group(1)) if d else None,
                "nodes": int(n.group(1)) if n else None,
                "score": (sc.group(1), int(sc.group(2))) if sc else None,
                "bestmove": bm}
    finally:
        try:
            s("quit"); p.wait(timeout=20)
        except Exception:
            p.kill()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("exe"); ap.add_argument("outdir")
    ap.add_argument("--settings", default="PC20", choices=["PC20", "S14", "none"])
    ap.add_argument("--reps", type=int, default=3)
    a = ap.parse_args()
    exe = os.path.realpath(a.exe)
    os.makedirs(a.outdir, exist_ok=True)
    settings = {"none": ["Hash 16", "Threads 1", "OwnBook false"],
                "S14": ["Hash 16", "Threads 1", "OwnBook false"] + S14,
                "PC20": ["Hash 16", "Threads 1", "OwnBook false"] + S14 + PC20X}[a.settings]

    out = {"exe": exe, "settings": a.settings, "threads": 1, "reps": a.reps,
           "sha256": subprocess.run(["sha256sum", exe], capture_output=True, text=True).stdout.split()[0],
           "date_utc": subprocess.run(["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"],
                                      capture_output=True, text=True).stdout.strip(),
           "cells": []}
    bad = []
    for fi, fen in enumerate(FENS):
        for limit in BUDGETS:
            reps = [run(exe, settings, fen, limit) for _ in range(a.reps)]
            tuples = {(r["bestmove"], r["score"], r["depth"], r["nodes"]) for r in reps}
            cell = {"pos": fi, "limit": limit, "variants": len(tuples),
                    "reproducible": len(tuples) == 1,
                    "detail": [{"bestmove": r["bestmove"], "score": r["score"],
                                "depth": r["depth"], "nodes": r["nodes"]} for r in reps]}
            out["cells"].append(cell)
            if not cell["reproducible"]:
                bad.append(cell)
            print("pos %d %-22s variants %d %s"
                  % (fi, limit, len(tuples), "" if len(tuples) == 1 else
                     str([(r["bestmove"], r["depth"], r["nodes"]) for r in reps])))

    total = len(out["cells"])
    rep = sum(1 for c in out["cells"] if c["reproducible"])
    out["summary"] = {"cells": total, "reproducible": rep,
                      "not_reproducible": total - rep,
                      "non_reproducible_list": [(c["pos"], c["limit"]) for c in bad]}
    with open(os.path.join(a.outdir, "label_repro.json"), "w") as f:
        json.dump(out, f, indent=2)
    print("\nreproducible: %d of %d cells (%d reps each)" % (rep, total, a.reps))
    if bad:
        print("NOT reproducible:")
        for c in bad:
            print("  pos %d %s -> %s" % (c["pos"], c["limit"], c["detail"]))


if __name__ == "__main__":
    main()
