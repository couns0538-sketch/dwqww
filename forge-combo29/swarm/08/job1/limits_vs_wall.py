#!/usr/bin/env python3
"""limits_vs_wall.py RAWDIR — recompute the engine's ClockPlan for each run from the formula in
include/forge/clock_plan.hpp (defaults TmSoftDivisor 22, TmIncrementPercent 75, TmHardPercent 60,
TmHardSoftMultiple 5, Move Overhead 10) and compare the measured wall time with soft and hard.
The formula is copied from the source at 6b98f217 by hand; the source lines are cited in the report.
"""
import json
import os
import sys

raw = sys.argv[1] if len(sys.argv) > 1 else "raw"
SOFT_DIV, INC_PCT, HARD_PCT, HARD_MULT, OVERHEAD = 22, 75, 60, 5, 10


def plan(time_ms, inc):
    if time_ms <= OVERHEAD:
        return 0, 0, True
    avail = time_ms - OVERHEAD
    soft = avail // SOFT_DIV + inc * INC_PCT // 100
    hard = min(avail * HARD_PCT // 100, soft * HARD_MULT)
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


runs = [("base_mt50_a.jsonl", "movetime 50", ("movetime", 50, 0)),
        ("mt500.jsonl", "movetime 500", ("movetime", 500, 0)),
        ("tc1000.jsonl", "wtime 1000 inc 10", ("clock", 1000, 10)),
        ("tc10000.jsonl", "wtime 10000 inc 100", ("clock", 10000, 100))]

ALIAS = {"base_mt50_a.jsonl": "base_a.jsonl", "base_mt50_b.jsonl": "base_b.jsonl"}


def resolve(name):
    p = os.path.join(raw, name)
    if os.path.exists(p):
        return p
    alt = ALIAS.get(name)
    if alt and os.path.exists(os.path.join(raw, alt)):
        return os.path.join(raw, alt)
    return None

print("| run | engine soft ms | engine hard ms | median wall | p99 wall | max wall | n over hard | n over soft |")
print("|---|---|---|---|---|---|---|---|")
for fname, label, spec in runs:
    p = resolve(fname)
    if not p:
        continue
    recs = [json.loads(l) for l in open(p) if l.strip()]
    w = [r["wall_ms"] for r in recs]
    if spec[0] == "movetime":
        soft = hard = max(1, spec[1] - OVERHEAD)
    else:
        soft, hard, empty = plan(spec[1], spec[2])
        assert not empty
    print("| %s | %d | %d | %.1f | %.1f | %.1f | %d | %d |" %
          (label, soft, hard, pct(w, 50), pct(w, 99), max(w),
           sum(1 for x in w if x > hard), sum(1 for x in w if x > soft)))

print()
print("## how much of the hard limit is used (movetime runs: hard = movetime - Move Overhead 10)")
for fname, label, spec in runs:
    p = resolve(fname)
    if not p:
        continue
    recs = [json.loads(l) for l in open(p) if l.strip()]
    w = [r["wall_ms"] for r in recs if r["wall_ms"] > 5.0]  # drop the one book answer
    if spec[0] == "movetime":
        hard = max(1, spec[1] - OVERHEAD)
    else:
        soft, hard, _ = plan(spec[1], spec[2])
    print("| %s | wall/hard median %.3f | wall/hard max %.3f |" % (label, pct(w, 50) / hard, max(w) / hard))
