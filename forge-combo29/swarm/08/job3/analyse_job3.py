#!/usr/bin/env python3
"""analyse_job3.py RAWDIR — AREA 8 job 3: movestogo 1, 2, 40 with wtime 1000, plus a same-session
no-movestogo control. Reads only the committed raw files. Also recomputes the plan from clock_plan.hpp.
"""
import json
import os
import sys

import chess

raw = sys.argv[1] if len(sys.argv) > 1 else "raw"
OVERHEAD = 10


def plan(time_ms, inc, mtg, div=22, incpct=75, hardpct=60, mult=5):
    if time_ms <= OVERHEAD:
        return 0, 0, True
    avail = time_ms - OVERHEAD
    if mtg and mtg > 0:
        m = mtg if mtg < 50 else 50
        soft = avail // (m + 1) + inc * 3 // 4
        hard = min(avail * 4 // 5, soft * 4)
    else:
        soft = avail // div + inc * incpct // 100
        hard = min(avail * hardpct // 100, soft * mult)
    soft = max(1, min(soft, avail))
    hard = max(1, min(hard, avail))
    if soft > hard:
        soft = hard
    return soft, hard, False


def pct(v, p):
    s = sorted(v)
    k = (len(s) - 1) * p / 100.0
    lo = int(k)
    hi = min(lo + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (k - lo)


runs = [("mtg1.jsonl", 1), ("mtg2.jsonl", 2), ("mtg40.jsonl", 40), ("mtg_none.jsonl", 0)]

print("## job 3 — movestogo with wtime 1000 btime 1000, no increment. 200 searches per control.")
print()
print("| movestogo | engine soft ms | engine hard ms | median ms | p99 ms | max ms | median / 1000 ms clock | over its hard | over 1000 ms clock | illegal bestmoves |")
print("|---|---|---|---|---|---|---|---|---|---|")
for fname, mtg in runs:
    p = os.path.join(raw, fname)
    if not os.path.exists(p):
        print("| %s | missing | | | | | | | | |" % fname)
        continue
    recs = [json.loads(l) for l in open(p) if l.strip()]
    w = [r["wall_ms"] for r in recs]
    soft, hard, empty = plan(1000, 0, mtg)
    bad = 0
    for r in recs:
        try:
            b = chess.Board(r["fen"])
        except Exception:
            bad += 1
            continue
        tok = r["bestmove"].split()
        if len(tok) < 2 or (b.legal_moves and tok[1] not in {b.uci(m) for m in b.legal_moves}):
            bad += 1
    label = str(mtg) if mtg else "none (control)"
    print("| %s | %d | %d | %.2f | %.2f | %.2f | %.1f %% | %d | %d | %d |" %
          (label, soft, hard, pct(w, 50), pct(w, 99), max(w), 100.0 * pct(w, 50) / 1000.0,
           sum(1 for x in w if x > hard), sum(1 for x in w if x > 1000), bad))

print()
print("## control: is the moves_to_go branch read at all? movestogo 1 vs 2 vs 40 vs none")
print("| comparison | median A ms | median B ms | ratio |")
print("|---|---|---|---|")
vals = {}
for fname, mtg in runs:
    p = os.path.join(raw, fname)
    if os.path.exists(p):
        vals[mtg] = pct([json.loads(l)["wall_ms"] for l in open(p) if l.strip()], 50)
for a, b in [(1, 2), (1, 40), (1, 0), (40, 0)]:
    if a in vals and b in vals:
        print("| movestogo %s / %s | %.2f | %.2f | %.2f |" % (a, b, vals[a], vals[b],
                                                              vals[a] / vals[b] if vals[b] else float("nan")))
