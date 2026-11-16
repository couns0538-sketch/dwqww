#!/usr/bin/env python3
"""analyse_job5.py RAWDIR — the clock-tail scaling sweep. Reads only committed raw files."""
import json
import os
import sys

raw = sys.argv[1] if len(sys.argv) > 1 else "raw"
CLOCKS = [200, 500, 1000, 3000, 10000, 30000]
SOFT_DIV, OVERHEAD = 22, 10


def pct(v, p):
    s = sorted(v)
    k = (len(s) - 1) * p / 100.0
    lo = int(k)
    hi = min(lo + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (k - lo)


def plan(t):
    if t <= OVERHEAD:
        return 0, 0, True
    avail = t - OVERHEAD
    soft = avail // SOFT_DIV
    hard = min(avail * 60 // 100, soft * 5)
    soft = max(1, min(soft, avail))
    hard = max(1, min(hard, avail))
    if soft > hard:
        soft = hard
    return soft, hard, False


print("## the clock-tail sweep — wtime/btime T, winc 0, 200 searches per clock, OwnBook false")
print()
print("| clock ms | soft plan | hard plan | median | p99 | max | p99/median | median/soft | over hard | over the clock |")
print("|---|---|---|---|---|---|---|---|---|---|")
rows = {}
for t in CLOCKS:
    p = os.path.join(raw, "t%d.jsonl" % t)
    if not os.path.exists(p):
        print("| %d | (missing) | | | | | | | | |" % t)
        continue
    recs = [json.loads(l) for l in open(p) if l.strip()]
    if len(recs) < 10:
        print("| %d | (only %d records, still running) | | | | | | | | |" % (t, len(recs)))
        continue
    w = [r["wall_ms"] for r in recs]
    soft, hard, _ = plan(t)
    med, p99 = pct(w, 50), pct(w, 99)
    rows[t] = (len(recs), med, p99, max(w))
    print("| %d | %d | %d | %.1f | %.1f | %.1f | %.1f | %.0f %% | %d | %d |" %
          (t, soft, hard, med, p99, max(w), p99 / med, 100.0 * med / soft,
           sum(1 for x in w if x > hard), sum(1 for x in w if x > t)))

print()
print("## does the tail SCALE with the clock? (the prediction's test)")
print("| pair | p99 ratio | median ratio | clock ratio |")
print("|---|---|---|---|")
for a, b in [(1000, 10000), (1000, 30000), (200, 10000)]:
    if a in rows and b in rows:
        print("| %d -> %d | %.1f | %.1f | %.0f |" %
              (a, b, rows[b][2] / rows[a][2], rows[b][1] / rows[a][1], b / a))

print()
print("## is the median a constant FRACTION of soft across clock sizes? (08-F9 generalisation)")
if rows:
    fr = [100.0 * rows[t][1] / plan(t)[0] for t in rows]
    print("| clock | median | soft | median/soft |")
    print("|---|---|---|---|")
    for t in rows:
        print("| %d | %.1f | %d | %.0f %% |" % (t, rows[t][1], plan(t)[0], 100.0 * rows[t][1] / plan(t)[0]))
    print()
    print("median/soft ranges %.0f %% to %.0f %% across the sweep (ratio of max to min %.1fx)" %
          (min(fr), max(fr), max(fr) / min(fr)))
