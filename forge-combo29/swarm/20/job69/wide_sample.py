#!/usr/bin/env python3
"""wide_sample.py — seat 20 job 69: the own-8MB variant on a WIDER sample, against a working reference.

S-F58 passed on 5 positions with a 47 cp worst case. The stated next step was "a wider sample at a stated
tolerance". This runs 20 G-set positions and reports the distribution of the alternate-line difference against the
HEALTHY build (Hash 16), not the collapsed one.

Tolerance stated BEFORE measuring: the candidate passes if the 90th percentile of |difference| across all
(positions x alternate lines) is <= 100 cp AND no single line moves more than 500 cp. Those are my judgement calls,
labelled as such, so an owner can substitute their own and re-read the same distribution.

usage: wide_sample.py <repaired-exe> <candidate-exe> <outdir> [n]
"""
import json
import os
import re
import statistics
import sys

import chess

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "AUDIT"))
from hardened import Engine  # noqa: E402

REF, CAND, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
N = int(sys.argv[4]) if len(sys.argv) > 4 else 20
os.makedirs(OUT, exist_ok=True)
S14 = [("Threads", 1), ("LmrQuietBase", 93), ("LmrQuietDivisor", 205), ("LmrNoisyBase", 13),
       ("LmrNoisyDivisor", 333), ("LmrHistoryDivisor", 5643), ("NullMoveBase", 5), ("LmpBase", 8),
       ("HistoryPruneMultiplier", 2220), ("HistoryBonusQuadratic", 24), ("HistoryBonusLinear", 54),
       ("HistoryBonusMax", 2212), ("SingularDepth", 6), ("IirDepth", 2), ("NonPawnCorrection", "true"),
       ("OwnBook", "false"), ("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
       ("CorrHistV2", "true"), ("MateAlphaGuard", "true")]
GO = "go wtime 5000 btime 5000"

GF = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "job24", "G_353.fens")
fens = []
for line in open(GF, encoding="utf-8", errors="replace"):
    if not line.strip():
        continue
    f = " ".join(line.split()[:6])
    try:
        b = chess.Board(f)
        if b.is_valid() and not b.is_game_over() and b.legal_moves.count() > 8 and not b.is_check():
            fens.append(f)
    except ValueError:
        pass
    if len(fens) >= N:
        break


def run(exe, fen, h):
    e = Engine(exe, opts=[("Hash", h), ("MultiPV", 3)] + S14)
    try:
        e.position(fen, ready_timeout=120.0)
        e.search(GO, 180)
        lines = [x for x in e.since(0) if x.startswith("info depth")]
    finally:
        e.close()
    depth = max([int(m.group(1)) for x in lines for m in [re.search(r"depth (\d+)", x)] if m], default=0)
    per = {}
    for x in lines:
        mi = re.search(r"multipv (\d+)", x)
        sc = re.search(r"score (cp|mate) (-?\d+)", x)
        if mi and sc and sc.group(1) == "cp":
            per[int(mi.group(1))] = int(sc.group(2))
    return depth, per


print(f"reference {REF} at Hash 16 (healthy)   candidate {CAND} at Hash 2048")
print(f"{len(fens)} positions, MultiPV 3, {GO}, Threads 1")
print()
diffs = []
rows = []
print(f"{'pos':>3s} {'ref depth':>9s} {'cand depth':>10s} {'lines compared':>14s} {'max |diff|':>10s}")
for i, f in enumerate(fens, 1):
    dr, ref = run(REF, f, 16)
    dc, cand = run(CAND, f, 2048)
    common = [k for k in ref if k in cand]
    d = [abs(cand[k] - ref[k]) for k in common]
    mx = max(d, default=0)
    diffs += d
    rows.append({"pos": i, "ref_depth": dr, "cand_depth": dc, "ref": ref, "cand": cand, "max_diff": mx})
    print(f"{i:3d} {dr:9d} {dc:10d} {len(common):14d} {mx:10d}")

print()
if diffs:
    diffs_sorted = sorted(diffs)
    p90 = diffs_sorted[int(0.9 * (len(diffs_sorted) - 1))]
    print(f"alternate-line comparisons: {len(diffs)}")
    print(f"  median |diff| {statistics.median(diffs):.0f} cp")
    print(f"  90th pct  |diff| {p90} cp")
    print(f"  max       |diff| {max(diffs)} cp")
    print(f"  within 10 cp: {sum(1 for d in diffs if d <= 10)}/{len(diffs)}")
    ok = p90 <= 100 and max(diffs) <= 500
    print()
    print(f"  PRE-STATED TOLERANCE (p90 <= 100 and max <= 500): {'PASS' if ok else 'FAIL'}")
    print(f"  main-line depth: reference median {statistics.median([r['ref_depth'] for r in rows]):.0f}, "
          f"candidate median {statistics.median([r['cand_depth'] for r in rows]):.0f}")

with open(os.path.join(OUT, "wide_sample.json"), "w") as f:
    json.dump({"rows": rows, "diffs": diffs}, f, indent=1)
print("\nwrote wide_sample.json")
