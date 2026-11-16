#!/usr/bin/env python3
"""repair_at_safe_hashes.py — seat 20 job 64: does the tt.clear repair help at the SAFE Hash sizes too?

S-C35 confirmed the repair at Hash 256/512 (where the shipped build collapses). But the owner's realistic MultiPV
settings are the SAFE ones — Hash 16, 64, 128 at MultiPV 3 — where the shipped build already works. Two questions
that decide whether the patch is worth taking for analysis:

  Q1 does the repair COST anything at the safe sizes (fewer depth for the same clock)?
  Q2 does it BUY anything there (more depth)?

Protocol: 10 G-set positions per cell, `go wtime 5000`, Threads 1, Hash 16/64/128, MultiPV 3, SHIPPED vs REPAIRED,
one run per position (the effect at safe sizes is small, so I also report the full depth list, not just the median).

Decision rule stated before measuring: if the repaired median depth is LOWER at any safe Hash by more than 1 ply, the
patch has a cost to declare; if equal or higher, it is a free improvement or neutral.

usage: repair_at_safe_hashes.py <shipped-exe> <repaired-exe> <outdir>
"""
import json
import os
import re
import statistics
import sys

import chess

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "AUDIT"))
from hardened import Engine  # noqa: E402

SHIP, FIX, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
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
    if len(fens) >= 10:
        break


def depth_of(lines):
    return max([int(m.group(1)) for x in lines for m in [re.search(r"depth (\d+)", x)] if m], default=0)


def arm(exe, h):
    ds = []
    for f in fens:
        e = Engine(exe, opts=[("Hash", h), ("MultiPV", 3)] + S14)
        try:
            e.position(f, ready_timeout=90.0)
            e.search(GO, 180)
            ds.append(depth_of(e.since(0)))
        finally:
            e.close()
    return ds


rows = []
print(f"shipped  {SHIP}")
print(f"repaired {FIX}")
print(f"MultiPV 3, {GO}, Threads 1, {len(fens)} G positions, one run each")
print()
print(f"{'Hash':>6s} {'build':9s} {'depths':>44s} {'median':>7s}")
for h in (16, 64, 128):
    for label, exe in (("shipped", SHIP), ("repaired", FIX)):
        ds = arm(exe, h)
        rows.append({"hash": h, "build": label, "depths": ds, "median": statistics.median(ds)})
        print(f"{h:6d} {label:9s} {str(ds):>44s} {statistics.median(ds):>7.1f}")

print()
print("== verdict per Hash (rule: repaired lower by >1 ply = a cost to declare)")
for h in (16, 64, 128):
    s = next(r for r in rows if r["hash"] == h and r["build"] == "shipped")["median"]
    f = next(r for r in rows if r["hash"] == h and r["build"] == "repaired")["median"]
    d = f - s
    verdict = ("COST to declare" if d < -1 else ("improvement" if d > 1 else "neutral"))
    print(f"  Hash {h:4d}: shipped {s:.1f}, repaired {f:.1f}, diff {d:+.1f} -> {verdict}")

with open(os.path.join(OUT, "repair_safe.json"), "w") as f:
    json.dump({"rows": rows}, f, indent=1)
print("\nwrote repair_safe.json")
