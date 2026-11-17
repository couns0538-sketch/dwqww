#!/usr/bin/env python3
"""deep_endgame.py — seat 20 job 71: the last open gap — does an 8 MB alternate table hold on DEEP endgames?

S-C44 left one honest gap: "20 seconds is not a 40-move game; a table that holds at depth 20 may not at depth 35."
This tests exactly that by selecting ENDGAME-ish G-set positions (low material, where searches run deep) and running
a long clock, comparing the own-8MB candidate (Hash 2048) against the healthy reference (Hash 16).

Pre-stated tolerance, same as S-C43: pass if p90 |diff| <= 100 cp and max <= 500 cp. Additionally I record the
deepest depth reached, because the whole point is whether depth 30+ changes the picture.

usage: deep_endgame.py <ref-exe> <cand-exe> <outdir> [n] [clock_ms]
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
N = int(sys.argv[4]) if len(sys.argv) > 4 else 12
CLOCK = int(sys.argv[5]) if len(sys.argv) > 5 else 10000
os.makedirs(OUT, exist_ok=True)
S14 = [("Threads", 1), ("LmrQuietBase", 93), ("LmrQuietDivisor", 205), ("LmrNoisyBase", 13),
       ("LmrNoisyDivisor", 333), ("LmrHistoryDivisor", 5643), ("NullMoveBase", 5), ("LmpBase", 8),
       ("HistoryPruneMultiplier", 2220), ("HistoryBonusQuadratic", 24), ("HistoryBonusLinear", 54),
       ("HistoryBonusMax", 2212), ("SingularDepth", 6), ("IirDepth", 2), ("NonPawnCorrection", "true"),
       ("OwnBook", "false"), ("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
       ("CorrHistV2", "true"), ("MateAlphaGuard", "true")]
GO = f"go wtime {CLOCK} btime {CLOCK}"

VAL = {chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3, chess.ROOK: 5, chess.QUEEN: 9}


def material(b):
    return sum(len(b.pieces(pt, c)) * v for pt, v in VAL.items() for c in (True, False))


GF = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "job24", "G_353.fens")
fens = []
for line in open(GF, encoding="utf-8", errors="replace"):
    if not line.strip():
        continue
    f = " ".join(line.split()[:6])
    try:
        b = chess.Board(f)
        if b.is_valid() and not b.is_game_over() and b.legal_moves.count() > 4 and material(b) <= 20:
            fens.append(f)
    except ValueError:
        pass
    if len(fens) >= N:
        break


def run(exe, fen, h):
    e = Engine(exe, opts=[("Hash", h), ("MultiPV", 3)] + S14)
    try:
        e.position(fen, ready_timeout=180.0)
        e.search(GO, 600)
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


print(f"{len(fens)} ENDGAME-ish positions (material <= 20), clock {CLOCK} ms, MultiPV 3, Threads 1")
print(f"reference {REF} at Hash 16; candidate {CAND} at Hash 2048")
print()
diffs = []
rows = []
print(f"{'pos':>3s} {'ref depth':>9s} {'cand depth':>10s} {'max |diff|':>10s}")
for i, f in enumerate(fens, 1):
    dr, ref = run(REF, f, 16)
    dc, cand = run(CAND, f, 2048)
    common = [k for k in ref if k in cand]
    d = [abs(cand[k] - ref[k]) for k in common]
    mx = max(d, default=0)
    diffs += d
    rows.append({"pos": i, "ref_depth": dr, "cand_depth": dc, "max_diff": mx, "ref": ref, "cand": cand})
    print(f"{i:3d} {dr:9d} {dc:10d} {mx:10d}")

print()
if diffs:
    ds = sorted(diffs)
    p90 = ds[int(0.9 * (len(ds) - 1))]
    print(f"comparisons {len(diffs)}  median {statistics.median(diffs):.0f} cp  p90 {p90} cp  max {max(diffs)} cp")
    print(f"deepest depth reached: reference {max(r['ref_depth'] for r in rows)}, "
          f"candidate {max(r['cand_depth'] for r in rows)}")
    ok = p90 <= 100 and max(diffs) <= 500
    print(f"PRE-STATED TOLERANCE: {'PASS' if ok else 'FAIL'}")

with open(os.path.join(OUT, "deep_endgame.json"), "w") as f:
    json.dump({"clock_ms": CLOCK, "rows": rows, "diffs": diffs}, f, indent=1)
print("\nwrote deep_endgame.json")
