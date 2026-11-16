#!/usr/bin/env python3
"""repro_s06f6.py — seat 20 job 24: run seat 06's OWN position set under their OWN settings.

The conflict: they report 101/353 (28.6 %) bestmove asymmetry at depth 10 on G; I measured 2/20 (10.0 %) on my own
20 positions. Rather than compare quoted numbers, this runs THEIR committed G_353.fens with THEIR stated settings:
  depth 10, S14 (14 setoptions), Threads 1, Hash 16, ucinewgame + isready before every go, OwnBook false.
Process discipline is recorded explicitly so the two can be compared:
  ARM "fresh": a fresh process per search (what I did in job19)
  ARM "shared": one process with ucinewgame before each go (what their report says they did)
Also reports a Wilson 95 % interval on each rate, because 2/20 and 101/353 are not comparable as bare percentages.

usage: repro_s06f6.py <exe> <outdir> [n] [arm]
"""
import json
import math
import os
import sys

import chess

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "AUDIT"))
from hardened import Engine  # noqa: E402

EXE, OUT = sys.argv[1], sys.argv[2]
N = int(sys.argv[3]) if len(sys.argv) > 3 else 353
ARM = sys.argv[4] if len(sys.argv) > 4 else "fresh"
os.makedirs(OUT, exist_ok=True)

FENS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "G_353.fens")
S14 = [("LmrQuietBase", 93), ("LmrQuietDivisor", 205), ("LmrNoisyBase", 13), ("LmrNoisyDivisor", 333),
       ("LmrHistoryDivisor", 5643), ("NullMoveBase", 5), ("LmpBase", 8), ("HistoryPruneMultiplier", 2220),
       ("HistoryBonusQuadratic", 24), ("HistoryBonusLinear", 54), ("HistoryBonusMax", 2212),
       ("SingularDepth", 6), ("IirDepth", 2), ("NonPawnCorrection", "true")]
# their stated settings
BASE = [("Threads", 1), ("Hash", 16)] + S14


def mirror_uci(u):
    if not u or u == "0000":
        return u
    return u[0] + str(9 - int(u[1])) + u[2] + str(9 - int(u[3])) + u[4:]


def score_of(s):
    if not s:
        return None, None
    p = s.split()
    if p[0] == "cp":
        return "cp", int(p[1])
    if p[0] == "mate":
        return "mate", int(p[1])
    return None, None


def wilson(k, n):
    if n == 0:
        return (0.0, 0.0)
    z = 1.959964
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


fens = [" ".join(l.split()[:6]) for l in open(FENS, encoding="utf-8", errors="replace") if l.strip()][:N]
rows = []
print(f"exe {EXE}")
print(f"positions: {len(fens)} from seat 06's G_353.fens")
print(f"settings: depth 10, S14 ({len(S14)} options), Threads 1, Hash 16, OwnBook false")
print(f"arm: {ARM}")
print()

shared = Engine(EXE, opts=BASE) if ARM == "shared" else None
try:
    for i, fen in enumerate(fens):
        P = chess.Board(fen)
        M = P.mirror()
        if ARM == "fresh":
            e1 = Engine(EXE, opts=BASE)
            try:
                e1.position(P.fen())
                rp = e1.search("go depth 10", 300)
            finally:
                e1.close()
            e2 = Engine(EXE, opts=BASE)
            try:
                e2.position(M.fen())
                rm = e2.search("go depth 10", 300)
            finally:
                e2.close()
        else:
            shared.send("ucinewgame")
            shared.isready()
            shared.position(P.fen())
            rp = shared.search("go depth 10", 300)
            shared.send("ucinewgame")
            shared.isready()
            shared.position(M.fen())
            rm = shared.search("go depth 10", 300)
        assert rp["bestmove"] and rp["score"] and rm["bestmove"] and rm["score"], \
            f"unparsed result at index {i} — refusing to record"
        want = mirror_uci(rp["bestmove"])
        ks, vs = score_of(rp["score"])
        km, vm = score_of(rm["score"])
        rows.append({"index": i, "fen": P.fen(), "p_best": rp["bestmove"], "m_best": rm["bestmove"],
                     "mirror_of_p": want, "bm_symmetric": want == rm["bestmove"],
                     "p_score": rp["score"], "m_score": rm["score"],
                     "sc_symmetric": (ks == km and vs == vm)})
        if (i + 1) % 50 == 0:
            bm = sum(1 for r in rows if not r["bm_symmetric"])
            print(f"  {i+1}/{len(fens)} done: bestmove asymmetric {bm} ({(100.0*bm/(i+1)):.1f} %)")
finally:
    if shared is not None:
        shared.close()

n = len(rows)
bm_asym = sum(1 for r in rows if not r["bm_symmetric"])
sc_asym = sum(1 for r in rows if not r["sc_symmetric"])
lo, hi = wilson(bm_asym, n)
print()
print(f"RESULT ({ARM}): bestmove asymmetric {bm_asym}/{n} = {100.0*bm_asym/n:.1f} %  "
      f"(Wilson 95 % CI {100*lo:.1f}–{100*hi:.1f} %)")
print(f"                score    asymmetric {sc_asym}/{n} = {100.0*sc_asym/n:.1f} %")
with open(os.path.join(OUT, f"repro_s06f6_{ARM}.json"), "w") as f:
    json.dump({"exe": EXE, "arm": ARM, "n": n, "fens_source": "seat06 job3 G_353.fens",
               "settings": "depth 10, S14, Threads 1, Hash 16, OwnBook false",
               "bm_asym": bm_asym, "sc_asym": sc_asym, "wilson": [lo, hi], "rows": rows}, f, indent=1)
print(f"\nwrote repro_s06f6_{ARM}.json")
