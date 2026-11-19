#!/usr/bin/env python3
"""kimi5 job 33: sum the per-search HP33 counter arrays of one replay jsonl.
Prints how many lines it summed, every named sum, the hp27 sum (the known-answer twin of
'fired'), and the derived shares of the job's table. Field order of the hp33 array (the
counting build's print, documented in split_counter.patch.txt):
0 eligible, 1 fired, 2 pivM, 3 pivW, 4 pivC, 5 none, 6 mNeg, 7 wNeg, 8 cNeg,
9 sumM, 10 sumW, 11 sumC, 12 firedStaleM, 13 firedStaleW, 14 pivWstaleW, 15 pivMstaleM,
16 eligStaleNzW, 17 eligStaleNzM, 18 mismatch.
Usage: agg_hp33.py <file.jsonl>
"""
import json
import sys

NAMES = ["eligible", "fired", "pivM", "pivW", "pivC", "none", "mNeg", "wNeg", "cNeg",
         "sumM", "sumW", "sumC", "firedStaleM", "firedStaleW", "pivWstaleW", "pivMstaleM",
         "eligStaleNzW", "eligStaleNzM", "mismatch"]

path = sys.argv[1]
sums = [0] * 19
n = 0
hp27_sum = 0
node_sum = 0
with open(path) as f:
    for line in f:
        row = json.loads(line)
        arr = row["hp33"]
        assert len(arr) == 19, f"bad hp33 length in {path}: {len(arr)}"
        for i, v in enumerate(arr):
            sums[i] += v
        hp27_sum += row["hp27"]
        node_sum += row["nodes"]
        n += 1

s = dict(zip(NAMES, sums))
print(f"lines summed: {n}  (file: {path})")
print(f"hp27 sum: {hp27_sum}   node sum: {node_sum}")
for name, v in s.items():
    print(f"{name}: {v}")
fired = s["fired"]
if fired:
    print(f"fired per 1000 eligible: {fired * 1000 / s['eligible']:.2f}")
    print(f"shares of fired: pivM {s['pivM'] / fired:.4f}  pivW {s['pivW'] / fired:.4f}  "
          f"pivC {s['pivC'] / fired:.4f}  none {s['none'] / fired:.4f}")
    print(f"means over fired: M {s['sumM'] / fired:.2f}  W {s['sumW'] / fired:.2f}  C1+C2 {s['sumC'] / fired:.2f}")
    print(f"fired with staleM {s['firedStaleM'] / fired:.4f}  staleW {s['firedStaleW'] / fired:.4f}")
    if s["pivW"]:
        print(f"pivotal-W with stale W: {s['pivWstaleW'] / s['pivW']:.4f} ({s['pivWstaleW']}/{s['pivW']})")
    if s["pivM"]:
        print(f"pivotal-M with stale M: {s['pivMstaleM'] / s['pivM']:.4f} ({s['pivMstaleM']}/{s['pivM']})")
if s["eligible"]:
    print(f"eligible stale-nonzero-W reads per 1000 eligible: {s['eligStaleNzW'] * 1000 / s['eligible']:.3f}")
    print(f"eligible stale-nonzero-M reads per 1000 eligible: {s['eligStaleNzM'] * 1000 / s['eligible']:.3f}")
print(f"fired == hp27 sum: {fired == hp27_sum} ({fired} vs {hp27_sum})")
print(f"mismatch: {s['mismatch']}")
