#!/usr/bin/env python3
"""analyse_pc20.py RAWDIR — PC build (r15) under PC20, Threads 1. Compares with the base-tree numbers."""
import json
import os
import sys

raw = sys.argv[1] if len(sys.argv) > 1 else "raw"


def load(name):
    p = os.path.join(raw, name)
    if not os.path.exists(p):
        return None
    return [json.loads(l) for l in open(p) if l.strip()]


def pct(v, p):
    s = sorted(v)
    k = (len(s) - 1) * p / 100.0
    lo = int(k)
    hi = min(lo + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (k - lo)


def plan_clock(t, overhead=10, div=22, hardpct=60, mult=5):
    if t <= overhead:
        return 0, 0, True
    avail = t - overhead
    soft = avail // div
    hard = min(avail * hardpct // 100, soft * mult)
    soft = max(1, min(soft, avail))
    hard = max(1, min(hard, avail))
    if soft > hard:
        soft = hard
    return soft, hard, False


BASE = {  # from my base-tree reports, same controls, Threads 1
    "movetime 50": 40.48, "movetime 500": 490.50,
    "wtime 1000 inc 0": 34.56, "wtime 10000 inc 0": 302.10,
}

rows = [("mt50_a.jsonl", "movetime 50", "none"), ("mt50_b.jsonl", "movetime 50", "none"),
        ("mt500.jsonl", "movetime 500", "none"),
        ("tc1000.jsonl", "wtime 1000 inc 0", "clock"), ("tc10000.jsonl", "wtime 10000 inc 0", "clock")]

print("## PC build r15 under PC20, Threads 1, Hash 16 — 200 searches per control (OG200)")
print()
print("| control | n | median ms | p99 ms | max ms | median last depth | base tree median | change |")
print("|---|---|---|---|---|---|---|---|")
for fname, label, kind in rows:
    recs = load(fname)
    if not recs or len(recs) < 50:
        print("| %s | (running: %d) | | | | | | |" % (label, len(recs or [])))
        continue
    w = [r["wall_ms"] for r in recs]
    med = pct(w, 50)
    depths = [r["last_depth"] for r in recs if r.get("last_depth")]
    b = BASE.get(label)
    print("| %s | %d | %.2f | %.2f | %.2f | %s | %s | %s |" %
          (label, len(recs), med, pct(w, 99), max(w),
           ("%d" % pct(depths, 50)) if depths else "-",
           ("%.2f" % b) if b else "-",
           ("%+.1f %% (%.2f ms)" % (100 * (med - b) / b, med - b)) if b else "-"))

print()
print("## 08-F2 test on the PC build: does `movetime T` still spend T - MoveOverhead on the wall clock?")
print("| control | plan (T-10) | median wall | median - plan |")
print("|---|---|---|---|")
for fname, label, kind in rows:
    if kind != "none":
        continue
    recs = load(fname)
    if not recs:
        continue
    t = 50 if "50" in label and "500" not in label else 500
    w = [r["wall_ms"] for r in recs if r["wall_ms"] > 1.0]
    if not w:
        continue
    print("| %s | %d | %.2f | %+.2f |" % (label, t - 10, pct(w, 50), pct(w, 50) - (t - 10)))

print()
print("## 08-F1/F10/F11 on the PC build: clocked tail and hard-limit behaviour")
print("| control | n | soft plan | hard plan | median | p99 | max | p99/median | over soft | over hard | over clock |")
print("|---|---|---|---|---|---|---|---|---|---|---|")
for fname, label, kind in rows:
    if kind != "clock":
        continue
    recs = load(fname)
    if not recs or len(recs) < 50:
        print("| %s | (running) | | | | | | | | | |" % label)
        continue
    t = 1000 if "1000 " in label + " " else 10000
    soft, hard, _ = plan_clock(t)
    w = [r["wall_ms"] for r in recs]
    print("| %s | %d | %d | %d | %.1f | %.1f | %.1f | %.1f | %d | %d | %d |" %
          (label, len(recs), soft, hard, pct(w, 50), pct(w, 99), max(w), pct(w, 99) / pct(w, 50),
           sum(1 for x in w if x > soft), sum(1 for x in w if x > hard), sum(1 for x in w if x > t)))

# movestogo (08-F8)
print()
print("## 08-F8 on the PC build: movestogo 1/2 at a 1000 ms clock, against the 792 ms hard limit")
print("| control | n | median | p99 | max | over the 792 ms hard limit |")
print("|---|---|---|---|---|---|")
for fname, label in [("mtg1.jsonl", "movestogo 1"), ("mtg2.jsonl", "movestogo 2")]:
    recs = load(fname)
    if not recs:
        continue
    w = [r["wall_ms"] for r in recs]
    print("| %s | %d | %.1f | %.1f | %.1f | %d |" % (label, len(recs), pct(w, 50), pct(w, 99), max(w),
                                                     sum(1 for x in w if x > 792)))
