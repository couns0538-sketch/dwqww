#!/usr/bin/env python3
"""class_test_2048.py — seat 20 job 52: is the Hash-2048 + MultiPV-8 quality defect ONE position or a CLASS?

S-C28 found on one board that Hash 2048 + MultiPV 8 plays `b8a8`, which is **46 cp worse** than the healthy move
(measured with `searchmoves` at Hash 16, depth 16, noise band ~24 cp, 5/5 stable). The owner asks for five more
positions: if the collapsed cell is worse beyond the noise band on MOST of them, it is a class defect and the
warning becomes emphatic; if it is worse on one and equal on four, the warning stays measured.

Protocol per position (Threads 1 throughout, fresh process per run):
  1. HEALTHY  : Hash 16, MultiPV 1, `go depth 16`  -> healthy move H and its score.
  2. COLLAPSED: Hash 2048, MultiPV 8, `go wtime 5000 btime 5000` (the condition that collapses; S-C27) -> move C.
  3. SCORE BOTH with `searchmoves` at healthy settings (Hash 16, MultiPV 1, depth 16), 3 runs each: s(H), s(C).
  4. NOISE BAND per position: MultiPV 4 score of H vs its restricted score (the restriction's own perturbation).
  5. DEFECT if s(C) is worse than s(H) by MORE than that position's noise band.

A "mate" score is converted to +/-30000 - n so comparisons still order correctly; positions with a mate at either
setting are reported separately rather than mixed into a centipawn delta.

usage: class_test_2048.py <pc-exe> <outdir> [n_positions]
"""
import json
import os
import re
import sys

import chess

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "AUDIT"))
from hardened import Engine  # noqa: E402

PC, OUT = sys.argv[1], sys.argv[2]
N = int(sys.argv[3]) if len(sys.argv) > 3 else 5
os.makedirs(OUT, exist_ok=True)

S14 = [("Threads", 1), ("LmrQuietBase", 93), ("LmrQuietDivisor", 205), ("LmrNoisyBase", 13),
       ("LmrNoisyDivisor", 333), ("LmrHistoryDivisor", 5643), ("NullMoveBase", 5), ("LmpBase", 8),
       ("HistoryPruneMultiplier", 2220), ("HistoryBonusQuadratic", 24), ("HistoryBonusLinear", 54),
       ("HistoryBonusMax", 2212), ("SingularDepth", 6), ("IirDepth", 2), ("NonPawnCorrection", "true"),
       ("OwnBook", "false"), ("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
       ("CorrHistV2", "true"), ("MateAlphaGuard", "true")]

HERE = os.path.dirname(os.path.abspath(__file__))
GF = os.path.join(HERE, "..", "job24", "G_353.fens")
fens = []
for line in open(GF, encoding="utf-8", errors="replace"):
    if not line.strip():
        continue
    f = " ".join(line.split()[:6])
    try:
        b = chess.Board(f)
        if b.is_valid() and not b.is_game_over() and b.legal_moves.count() > 8:
            fens.append(f)
    except ValueError:
        pass
    if len(fens) >= N:
        break
print(f"pc exe {PC}")
print(f"positions: {len(fens)} from the swarm G set")
print()


def val(score):
    """turn a score string into a comparable number; mate -> large magnitude."""
    if not score:
        return None
    p = score.split()
    if p[0] == "cp":
        return int(p[1])
    if p[0] == "mate":
        n = int(p[1])
        return (30000 - n * 100) if n > 0 else (-30000 - n * 100)
    return None


def search(fen, opts, go, runs=1):
    outs = []
    for _ in range(runs):
        e = Engine(PC, opts=list(opts))
        try:
            e.position(fen)
            r = e.search(go, 900)
        finally:
            e.close()
        outs.append(r)
    return outs


rows = []
print(f"{'#':>2s} {'healthy H':9s} {'score H':9s} {'collapsed C':11s} {'score C':9s} "
      f"{'delta':>7s} {'band':>5s} {'verdict':>10s}")
for i, fen in enumerate(fens, 1):
    # 1. healthy
    h = search(fen, [("Hash", 16), ("MultiPV", 1)] + S14, "go depth 16")[0]
    H = h["bestmove"]
    # 2. collapsed cell
    c = search(fen, [("Hash", 2048), ("MultiPV", 8)] + S14, "go wtime 5000 btime 5000", runs=2)
    C = c[0]["bestmove"]
    cdepth = len([x for x in []])  # not needed
    # 3. score both by restriction
    sh = search(fen, [("Hash", 16), ("MultiPV", 1)] + S14, f"go depth 16 searchmoves {H}", runs=3)
    sH = sh[0]["score"]
    sc = search(fen, [("Hash", 16), ("MultiPV", 1)] + S14, f"go depth 16 searchmoves {C}", runs=3)
    sC = sc[0]["score"]
    # 4. noise band: MultiPV 4 score for H vs restricted score for H
    mp = search(fen, [("Hash", 16), ("MultiPV", 4)] + S14, "go depth 16")[0]
    mp_score = None
    for ln in [x for x in [mp["last_info"]] if x]:
        m = re.search(r"score (cp|mate) (-?\d+)", ln)
        if m:
            mp_score = f"{m.group(1)} {m.group(2)}"
    band = None
    if mp_score and sH and mp_score.split()[0] == sH.split()[0] == "cp":
        band = abs(int(mp_score.split()[1]) - int(sH.split()[1]))
    vH, vC = val(sH), val(sC)
    delta = (vC - vH) if (vH is not None and vC is not None) else None
    if C == H:
        verdict = "SAME MOVE"
    elif delta is None or band is None:
        verdict = "UNSCORED"
    elif delta < -band:
        verdict = "WORSE"
    else:
        verdict = "equal"
    rows.append({"i": i, "fen": fen, "healthy_move": H, "healthy_score": sH,
                 "collapsed_move": C, "collapsed_score": sC, "delta_cp": delta,
                 "noise_band_cp": band, "verdict": verdict,
                 "collapsed_cell_depth_hint": c[0]["nodes"]})
    print(f"{i:2d} {H:9s} {str(sH):9s} {C:11s} {str(sC):9s} "
          f"{str(delta):>7s} {str(band):>5s} {verdict:>10s}")

worse = sum(1 for r in rows if r["verdict"] == "WORSE")
same = sum(1 for r in rows if r["verdict"] == "SAME MOVE")
equal = sum(1 for r in rows if r["verdict"] == "equal")
print()
print(f"summary over {len(rows)} positions: WORSE {worse}, equal-but-different {equal}, same move {same}")
print("class defect" if worse > len(rows) / 2 else "NOT a class defect by the pre-stated rule")

with open(os.path.join(OUT, "class_test_2048.json"), "w") as f:
    json.dump({"rows": rows, "worse": worse, "equal": equal, "same": same}, f, indent=1)
print("\nwrote class_test_2048.json")
