#!/usr/bin/env python3
"""analyse_job1.py RAWDIR — reads the raw JSONL of seat 08 job 1 and prints every table.
Nothing is typed by hand: all numbers below are computed from the committed raw files.
"""
import glob
import json
import os
import sys

raw = sys.argv[1] if len(sys.argv) > 1 else "raw"


def load(name):
    path = os.path.join(raw, name)
    return [json.loads(l) for l in open(path) if l.strip()]


def pct(vals, p):
    if not vals:
        return float("nan")
    s = sorted(vals)
    k = (len(s) - 1) * p / 100.0
    lo = int(k)
    hi = min(lo + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (k - lo)


def table(recs, label):
    w = [r["wall_ms"] for r in recs]
    over = sum(1 for r in recs if r["over_limit_50ms"])
    print("| %-26s | %4d | %8.1f | %8.1f | %9.1f | %8d | %5d |" %
          (label, len(w), pct(w, 50), pct(w, 99), max(w), sum(1 for r in recs if r["over_limit_50ms"]), over))
    return w


print("## runs on the machine (nproc = %d)" % os.cpu_count())
print()
print("| run                        |   n  | median ms | p99 ms  | largest ms | >limit+50ms |")
print("|----------------------------|------|-----------|---------|------------|-------------|")

sets = [("base_mt50_a.jsonl", "base A  movetime 50"),
        ("base_mt50_b.jsonl", "base B  movetime 50"),
        ("mt500.jsonl", "movetime 500"),
        ("tc1000.jsonl", "wtime/btime 1000 inc10"),
        ("tc10000.jsonl", "wtime/btime 10000 inc100")]
# the clean re-run names the baselines base_a / base_b; accept both spellings
ALIAS = {"base_mt50_a.jsonl": "base_a.jsonl", "base_mt50_b.jsonl": "base_b.jsonl"}


def resolve(name):
    p = os.path.join(raw, name)
    if os.path.exists(p):
        return p
    alt = ALIAS.get(name)
    if alt and os.path.exists(os.path.join(raw, alt)):
        return os.path.join(raw, alt)
    return None


data = {}
for f, lab in sets:
    p = resolve(f)
    if p:
        data[f] = table(load(os.path.basename(p)), lab)

# baseline repeatability
a = data.get("base_mt50_a.jsonl")
b = data.get("base_mt50_b.jsonl")
if a and b:
    print()
    print("## baseline repeatability (two identical runs of 200 x movetime 50)")
    ma, mb = pct(a, 50), pct(b, 50)
    print("| quantity | run A | run B | difference |")
    print("|---|---|---|---|")
    print("| median wall ms | %.1f | %.1f | %.1f |" % (ma, mb, abs(ma - mb)))
    print("| total ms | %.2f | %.2f | %.2f |" % (sum(a), sum(b), abs(sum(a) - sum(b))))
    print("| mean wall ms | %.2f | %.2f | %.2f |" % (sum(a) / len(a), sum(b) / len(b),
                                                     abs(sum(a) / len(a) - sum(b) / len(b))))
    print("| largest ms | %.1f | %.1f | %.1f |" % (max(a), max(b), abs(max(a) - max(b))))
    d = (sum(a) - sum(b)) / sum(b) * 100.0
    print("| total relative difference | | | %.2f %% |" % abs(d))

# per budget distribution detail
print()
print("## distribution detail, wall ms")
print("| run | min | p10 | p50 | p90 | p99 | max | mean | sd |")
print("|---|---|---|---|---|---|---|---|---|")
for f, lab in sets:
    if f not in data:
        continue
    w = data[f]
    mean = sum(w) / len(w)
    sd = (sum((x - mean) ** 2 for x in w) / (len(w) - 1)) ** 0.5
    print("| %s | %.1f | %.1f | %.1f | %.1f | %.1f | %.1f | %.1f | %.1f |" %
          (lab, min(w), pct(w, 10), pct(w, 50), pct(w, 90), pct(w, 99), max(w), mean, sd))

# overruns on the movetime runs expressed both ways
print()
print("## overruns (wall > budget + 50 ms) and over budget exactly")
print("| run | budget ms | n over budget+50 | n over budget | worst wall ms | worst excess ms |")
print("|---|---|---|---|---|---|")
for f, lab in sets:
    if f not in data or not data[f]:
        continue
    p = resolve(f)
    recs = load(os.path.basename(p))
    budget = recs[0]["limit_ms"]
    w = data[f]
    n50 = sum(1 for x in w if x > budget + 50.0)
    n0 = sum(1 for x in w if x > budget)
    print("| %s | %.0f | %d | %d | %.1f | %.1f |" % (lab, budget, n50, n0, max(w), max(w) - budget))
