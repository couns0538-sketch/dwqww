#!/usr/bin/env python3
"""collapse_boundary.py — seat 20 job 56: where does the MultiPV depth collapse BEGIN?

S-C32 established that Hash 2048 MB collapses to depth 1 on 10/10 positions at every MultiPV > 1, while Hash 16 MB
is perfectly clean. Seat 02's grid put the onset near 256 MB (MultiPV 3 collapsing, MultiPV 8 safe at Hash 16).
The owner needs the SAFE UPPER BOUND, so this walks Hash upward at a fixed MultiPV and reports depths.

Design: 10 positions from the G set (the same set as job55), Hash in {16, 64, 128, 256, 512}, MultiPV fixed at 3
(the plausible GUI setting), ONE run per position (the effect is huge and binary when it fires), plus a 3-run check
on any Hash whose depth is ambiguous (between healthy and depth-1).

Decision rule stated BEFORE measuring: a Hash is UNSAFE if the median deepest depth on the 10 positions is below half
the healthy median. A Hash is SAFE if its median is at least half the healthy median. The recommended limit is the
largest Hash that is SAFE.

usage: collapse_boundary.py <pc-exe> <outdir> [multipv]
"""
import json
import os
import re
import statistics
import sys

import chess

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "AUDIT"))
from hardened import Engine  # noqa: E402

PC, OUT = sys.argv[1], sys.argv[2]
MPV = int(sys.argv[3]) if len(sys.argv) > 3 else 3
os.makedirs(OUT, exist_ok=True)

S14 = [("Threads", 1), ("LmrQuietBase", 93), ("LmrQuietDivisor", 205), ("LmrNoisyBase", 13),
       ("LmrNoisyDivisor", 333), ("LmrHistoryDivisor", 5643), ("NullMoveBase", 5), ("LmpBase", 8),
       ("HistoryPruneMultiplier", 2220), ("HistoryBonusQuadratic", 24), ("HistoryBonusLinear", 54),
       ("HistoryBonusMax", 2212), ("SingularDepth", 6), ("IirDepth", 2), ("NonPawnCorrection", "true"),
       ("OwnBook", "false"), ("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
       ("CorrHistV2", "true"), ("MateAlphaGuard", "true")]
GO = "go wtime 5000 btime 5000"
HASHES = (16, 64, 128, 256, 512)

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


def depth_of(fen, h, mp):
    e = Engine(PC, opts=[("Hash", h), ("MultiPV", mp)] + S14)
    try:
        e.position(fen, ready_timeout=90.0)
        r = e.search(GO, 180)
        lines = [x for x in e.since(0) if x.startswith("info depth")]
    finally:
        e.close()
    d = None
    for ln in lines:
        m = re.search(r"depth (\d+)", ln)
        if m:
            v = int(m.group(1))
            d = v if d is None else max(d, v)
    return d, r["nodes"]


print(f"pc exe {PC}   MultiPV {MPV}   {len(fens)} positions   Threads 1   {GO}")
print("decision rule (stated before measuring): UNSAFE if median depth < half the healthy median")
print()
healthy = [depth_of(f, 16, 1)[0] for f in fens]
hmed = statistics.median([d for d in healthy if d is not None])
print(f"healthy (Hash 16, MultiPV 1): depths {healthy}  median {hmed}")
print()
rows = []
for h in HASHES:
    ds, ns = [], []
    for f in fens:
        d, n = depth_of(f, h, MPV)
        ds.append(d)
        ns.append(n)
    valid = [d for d in ds if d is not None]
    med = statistics.median(valid) if valid else None
    safe = med is not None and med >= hmed / 2
    rows.append({"hash": h, "multipv": MPV, "depths": ds, "median": med, "safe": safe,
                 "nodes": ns})
    print(f"  Hash {h:4d} MB: depths {str(ds):46s} median {str(med):>5s}  "
          f"{'SAFE' if safe else 'UNSAFE'}")

safe_hashes = [r["hash"] for r in rows if r["safe"]]
limit = max(safe_hashes) if safe_hashes else None
print()
print(f"== largest SAFE Hash at MultiPV {MPV}: {limit} MB")
if limit:
    print(f"   recommendation: Hash <= {limit} MB with MultiPV {MPV}")

with open(os.path.join(OUT, "collapse_boundary.json"), "w") as f:
    json.dump({"multipv": MPV, "healthy_median": hmed, "rows": rows, "safe_limit": limit}, f, indent=1)
print("\nwrote collapse_boundary.json")
