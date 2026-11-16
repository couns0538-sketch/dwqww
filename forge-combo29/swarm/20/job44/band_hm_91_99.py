#!/usr/bin/env python3
"""band_hm_91_99.py — seat 20 job 44: the fifty-move score band, halfmove 91..99, with PER-RUN data.

The owner wants the two live PC defects confirmed at Threads 1 with per-run data. This is the first: on the PC r15
build under PC20, what exactly happens to the score between halfmove 91 and 99 on a K+R v K board that is genuinely
won? My earlier sweeps sampled 89/90/91/95/99/100; this walks EVERY value 85..100 with 3 runs each, on both builds,
Threads 1.

Also plants the Rule-1 control: the same harness must show a DIFFERENT score somewhere in the band (it does — the
band edges differ), and a deliberately dead position (K v K) must give cp 0 everywhere, proving the sweep can see a
zero that is real.

usage: band_hm_91_99.py <base-exe> <pc-exe> <outdir>
"""
import json
import os
import sys

import chess

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "AUDIT"))
from hardened import Engine  # noqa: E402

BASE, PC, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
os.makedirs(OUT, exist_ok=True)

S14 = [("Threads", 1), ("Hash", 16), ("LmrQuietBase", 93), ("LmrQuietDivisor", 205), ("LmrNoisyBase", 13),
       ("LmrNoisyDivisor", 333), ("LmrHistoryDivisor", 5643), ("NullMoveBase", 5), ("LmpBase", 8),
       ("HistoryPruneMultiplier", 2220), ("HistoryBonusQuadratic", 24), ("HistoryBonusLinear", 54),
       ("HistoryBonusMax", 2212), ("SingularDepth", 6), ("IirDepth", 2), ("NonPawnCorrection", "true"),
       ("OwnBook", "false")]
PC20 = S14 + [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"), ("CorrHistV2", "true"),
              ("MateAlphaGuard", "true")]
KRK = "1K6/8/8/3R4/8/8/8/k7 w - - 0 1"     # genuinely won for White (K+R v K)
KVK = "8/8/8/8/8/8/7k/K7 w - - 0 1"       # genuinely dead (K v K) -> the control


def hm(fen, v):
    p = fen.split()
    p[4] = str(v)
    return " ".join(p)


def run(exe, opts, fen, go="go depth 10"):
    e = Engine(exe, opts=list(opts))
    try:
        e.position(fen)
        r = e.search(go, 400)
    finally:
        e.close()
    return r


rows = []
BUILDS = (("base_s14", BASE, S14), ("pc20", PC, PC20))
print(f"board (won) {KRK}")
print(f"board (dead control) {KVK}")
print(f"go depth 10, Threads 1, 3 runs per halfmove value")
print()
for label, exe, opts in BUILDS:
    print(f"=== {label}")
    print(f"{'hm':>4s} {'run1':>10s} {'run2':>10s} {'run3':>10s} {'stable':>7s} {'nodes':>10s} {'bestmove':9s}")
    for v in range(85, 101):
        outs = [run(exe, opts, hm(KRK, v)) for _ in range(3)]
        sc = [o["score"] for o in outs]
        nd = [o["nodes"] for o in outs]
        bm = [o["bestmove"] for o in outs]
        stable = len(set(sc)) == 1 and len(set(nd)) == 1
        rows.append({"build": label, "halfmove": v, "scores": sc, "nodes": nd, "bestmoves": bm,
                     "stable": stable})
        print(f"{v:4d} {sc[0]:>10s} {sc[1]:>10s} {sc[2]:>10s} {str(stable):>7s} {nd[0]:10d} {bm[0]:9s}")

print()
print("=== control: the dead board must be cp 0 at every value (proves a real zero is visible)")
for label, exe, opts in BUILDS:
    vals = []
    for v in (85, 91, 95, 99, 100):
        o = run(exe, opts, hm(KVK, v))
        vals.append(f"hm{v}:{o['score']}")
    print(f"  {label:9s} {'  '.join(vals)}")

with open(os.path.join(OUT, "band_hm.json"), "w") as f:
    json.dump({"won_board": KRK, "dead_board": KVK, "rows": rows}, f, indent=1)
print("\nwrote band_hm.json")
