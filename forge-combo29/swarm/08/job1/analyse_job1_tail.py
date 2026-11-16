#!/usr/bin/env python3
"""analyse_job1_tail.py RAWDIR — the tail and the instant searches, from the raw files only."""
import json
import os
import sys

raw = sys.argv[1] if len(sys.argv) > 1 else "raw"


def load(name):
    return [json.loads(l) for l in open(os.path.join(raw, name)) if l.strip()]


print("## instant searches (wall < 5 ms) — which ones and why")
print("| run | i | wall ms | bestmove | fen |")
print("|---|---|---|---|---|")
for name in ["base_mt50_a.jsonl", "base_mt50_b.jsonl", "mt500.jsonl", "tc1000.jsonl", "tc10000.jsonl"]:
    p = os.path.join(raw, name)
    if not os.path.exists(p):
        continue
    for r in load(name):
        if r["wall_ms"] < 5.0:
            print("| %s | %d | %.2f | %s | %s |" % (name, r["i"], r["wall_ms"], r["bestmove"], r["fen"]))

print()
print("## the 10 slowest searches of the 10000 ms clock run")
recs = sorted(load("tc10000.jsonl"), key=lambda r: -r["wall_ms"])[:10]
print("| i | wall ms | move-overhead-adjusted budget ms | bestmove | fen |")
print("|---|---|---|---|---|")
for r in recs:
    print("| %d | %.1f | %.0f | %s | %s |" % (r["i"], r["wall_ms"], r["limit_ms"], r["bestmove"], r["fen"]))

print()
print("## the 10 slowest searches of the 1000 ms clock run")
recs = sorted(load("tc1000.jsonl"), key=lambda r: -r["wall_ms"])[:10]
print("| i | wall ms | bestmove | fen |")
print("|---|---|---|---|")
for r in recs:
    print("| %d | %.1f | %s | %s |" % (r["i"], r["wall_ms"], r["bestmove"], r["fen"]))

print()
print("## is the slow tail the same positions in both clocked runs? (top 20 by wall time)")
a = load("tc1000.jsonl")
b = load("tc10000.jsonl")
top_a = {r["i"] for r in sorted(a, key=lambda r: -r["wall_ms"])[:20]}
top_b = {r["i"] for r in sorted(b, key=lambda r: -r["wall_ms"])[:20]}
print("| overlap of the two top-20 sets | %d of 20 |" % len(top_a & top_b))
print("| indices only in 1000 ms top-20 | %s |" % sorted(top_a - top_b))
print("| indices only in 10000 ms top-20 | %s |" % sorted(top_b - top_a))
