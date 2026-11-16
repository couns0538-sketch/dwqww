#!/usr/bin/env python3
"""analyse_job2.py RAWDIR — AREA 8 job 2: very little time. Reads only the committed raw files."""
import json
import os
import sys

import chess

raw = sys.argv[1] if len(sys.argv) > 1 else "raw2"
times = [100, 30, 10, 1, 0]
incs = [0, 10]


def pct(v, p):
    s = sorted(v)
    k = (len(s) - 1) * p / 100.0
    lo = int(k)
    hi = min(lo + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (k - lo)


def plan(time_ms, inc, overhead=10, div=22, incpct=75, hardpct=60, mult=5):
    if time_ms <= overhead:
        return 0, 0, True
    avail = time_ms - overhead
    soft = avail // div + inc * incpct // 100
    hard = min(avail * hardpct // 100, soft * mult)
    soft = max(1, min(soft, avail))
    hard = max(1, min(hard, avail))
    if soft > hard:
        soft = hard
    return soft, hard, False


print("## job 2 — very little time. 200 searches per control, first 100 O + first 100 G.")
print("`over the clock` = wall time greater than the wtime given (a GUI would flag the flag).")
print()
print("| time | inc | engine soft | engine hard | reserve empty | median ms | p99 ms | max ms | over the clock | over hard | bestmoves illegal |")
print("|---|---|---|---|---|---|---|---|---|---|---|")
rows = []
for t in times:
    for inc in incs:
        path = os.path.join(raw, "w%d_i%d.jsonl" % (t, inc))
        if not os.path.exists(path):
            print("| %d | %d | (missing %s) | | | | | | | | |" % (t, inc, path))
            continue
        recs = [json.loads(l) for l in open(path) if l.strip()]
        w = [r["wall_ms"] for r in recs]
        soft, hard, empty = plan(t, inc)
        over_clock = sum(1 for x in w if x > t)
        over_hard = sum(1 for x in w if not empty and x > hard)
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
        print("| %d | %d | %d | %d | %s | %.2f | %.2f | %.2f | %d | %d | %d |" %
              (t, inc, soft, hard, "YES" if empty else "no", pct(w, 50), pct(w, 99), max(w),
               over_clock, over_hard, bad))
        rows.append((t, inc, w, empty, soft, hard))

print()
print("## the inc-0 vs inc-10 comparison the prediction named")
print("| time | median inc 0 | median inc 10 | inc10 - inc0 | prediction said inc 10 is larger by > 2 ms |")
print("|---|---|---|---|---|")
for t in times:
    a = os.path.join(raw, "w%d_i0.jsonl" % t)
    b = os.path.join(raw, "w%d_i10.jsonl" % t)
    if not (os.path.exists(a) and os.path.exists(b)):
        continue
    wa = [json.loads(l)["wall_ms"] for l in open(a) if l.strip()]
    wb = [json.loads(l)["wall_ms"] for l in open(b) if l.strip()]
    d = pct(wb, 50) - pct(wa, 50)
    print("| %d | %.2f | %.2f | %+.2f | %s |" % (t, pct(wa, 50), pct(wb, 50), d,
                                                 "held" if d > 2.0 else "did NOT hold"))

print()
print("## what the engine actually answered at wtime 1 and 0 (the reserve-empty case)")
for t in (1, 0):
    for inc in incs:
        path = os.path.join(raw, "w%d_i%d.jsonl" % (t, inc))
        if not os.path.exists(path):
            continue
        recs = [json.loads(l) for l in open(path) if l.strip()]
        w = [r["wall_ms"] for r in recs]
        bms = {}
        for r in recs:
            bms[r["bestmove"]] = bms.get(r["bestmove"], 0) + 1
        print("| wtime %d inc %d | %d searches | wall min %.2f max %.2f | distinct bestmoves %d | most common %s |" %
              (t, inc, len(recs), min(w), max(w), len(bms), sorted(bms.items(), key=lambda kv: -kv[1])[0][0]))
