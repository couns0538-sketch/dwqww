#!/usr/bin/env python3
"""sums.py -- K13: the four big sums, measured with the EOF-safe interactive driver.

Protocol from the brief: plain build, S14, `ucinewgame` + `isready` before every `go`,
Threads 1, Hash 16, and the sum of each search's FINAL node count.

Two regimes, because the brief's "plain build, S14" is ambiguous:
  s14     : Threads 1 + Hash 16 + the 14 S14 setoptions
  default : Threads 1 + Hash 16 only   (this is the regime that reproduces the bench pins)

Usage: sums.py OUTDIR [depth12only]
"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from drv import Drv

EXE = os.environ.get("FORGE_EXE", "/home/ubuntu/builds/release/forge")
OUT = os.path.abspath(sys.argv[1])
SETS = os.path.join(OUT, "sets")
os.makedirs(os.path.join(OUT, "sums"), exist_ok=True)
D12ONLY = len(sys.argv) > 2 and sys.argv[2] == "depth12only"

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]

PUBLISHED = {"O": {12: 9500069, 14: 21812100}, "G": {12: 18466239, 14: 43345893}}
FIRST3_O = [41311, 24872, 28574]


def load(which):
    if which == "O":
        return [l.strip() for l in open(os.path.join(SETS, "first200.fens")) if l.strip()]
    return [l.strip().split(";")[0].strip()
            for l in open(os.path.join(SETS, "set_G.epd")) if l.strip()]


def run_regime(regime, which, depth):
    fens = load(which)
    d = Drv(EXE)
    d.uci()
    d.isready()
    d.opt("Threads", "1")
    d.opt("Hash", "16")
    if regime == "s14":
        for k, v in S14:
            d.opt(k, v)
    d.isready()
    rows = []
    t0 = time.monotonic()
    for i, fen in enumerate(fens):
        d.pos("position fen " + fen)
        d.write("ucinewgame")
        d.isready()
        nodes, best, lines = d.go("go depth %d" % depth)
        rows.append({"i": i, "fen": fen, "nodes": nodes, "bestmove": best})
        if i % 40 == 0:
            print("  %s %s d%d: %d/%d" % (regime, which, depth, i, len(fens)), flush=True)
    el = time.monotonic() - t0
    d.quit()
    tag = "sums/%s_%s_d%d.json" % (regime, which, depth)
    with open(os.path.join(OUT, tag), "w") as f:
        json.dump(rows, f, indent=1)
        f.write("\n")
    total = sum(r["nodes"] or 0 for r in rows)
    return {"positions": len(rows), "total": total,
            "published": PUBLISHED[which].get(depth),
            "match": total == PUBLISHED[which].get(depth),
            "first3": [r["nodes"] for r in rows[:3]],
            "null_nodes": sum(1 for r in rows if r["nodes"] is None),
            "seconds": round(el, 1)}


def main():
    out = {}
    for which in ("O", "G"):
        for regime in ("s14", "default"):
            depths = [12] if D12ONLY else [12, 14]
            for depth in depths:
                key = "%s_%s_d%d" % (which, regime, depth)
                print("running " + key, flush=True)
                out[key] = run_regime(regime, which, depth)
                out[key]["first3_O_expected"] = FIRST3_O if which == "O" else None
                print("  -> " + json.dumps(out[key]), flush=True)
                with open(os.path.join(OUT, "sums_summary.json"), "w") as f:
                    json.dump(out, f, indent=2)
                    f.write("\n")
    print(json.dumps(out, indent=2))


main()
