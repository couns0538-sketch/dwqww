#!/usr/bin/env python3
"""score_three_moves.py — seat 20 job 51: are `f6d7` and `b8a8` WORSE than `g7g6`, or merely different?

The collapsed MultiPV/Hash cells (S-C27) play different moves on
`1r6/2k2pp1/2p2n2/2Pppb1p/7P/1P2PPP1/P3BK2/R1R5 b - - 0 1`:
    healthy cells -> g7g6      Hash 256/MultiPV 8 -> f6d7      Hash 2048/MultiPV 3,8 -> b8a8

Method — TWO independent scorings, because each has a known weakness:

  A. MultiPV 4 at the HEALTHY settings (MultiPV 1-equivalent tree, Hash 16), `go depth 16`. MultiPV gives each root
     move's own score from ONE search, so no restriction is involved. Weakness: MultiPV itself changes the tree
     slightly, which is exactly what the collapse exploits — so this is the closest thing to "the engine's own
     opinion at good settings".
  B. Each move restricted with `searchmoves <move>` at Hash 16, `go depth 16`, MultiPV 1. Weakness: my own S-C23
     showed a restriction perturbs the score by a few cp, so treat these as a cross-check, not the primary number.

Verdict rule, stated BEFORE measuring: if the collapsed cells' moves are worse by MORE than the restriction's own
perturbation (measured as the difference between B's score for the healthy move and A's score for it), call it a
QUALITY defect; if the three scores fall within that band, call it "a different move, not a worse one".

usage: score_three_moves.py <pc-exe> <outdir>
"""
import json
import os
import re
import sys

import chess

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "AUDIT"))
from hardened import Engine  # noqa: E402

PC, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)

S14 = [("Threads", 1), ("LmrQuietBase", 93), ("LmrQuietDivisor", 205), ("LmrNoisyBase", 13),
       ("LmrNoisyDivisor", 333), ("LmrHistoryDivisor", 5643), ("NullMoveBase", 5), ("LmpBase", 8),
       ("HistoryPruneMultiplier", 2220), ("HistoryBonusQuadratic", 24), ("HistoryBonusLinear", 54),
       ("HistoryBonusMax", 2212), ("SingularDepth", 6), ("IirDepth", 2), ("NonPawnCorrection", "true"),
       ("OwnBook", "false"), ("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
       ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("Hash", 16)]
FEN = "1r6/2k2pp1/2p2n2/2Pppb1p/7P/1P2PPP1/P3BK2/R1R5 b - - 0 1"
MOVES = ["g7g6", "f6d7", "b8a8"]

board = chess.Board(FEN)
print(f"fen {FEN}")
print(f"side to move: {'white' if board.turn else 'black'}; legal moves {board.legal_moves.count()}")
for m in MOVES:
    print(f"  {m}: legal in this position = {chess.Move.from_uci(m) in board.legal_moves}")
print()


def score_moves_multipv(n, depth=16):
    """one search, MultiPV n, returns {move: score} for the root lines."""
    e = Engine(PC, opts=[("MultiPV", n)] + S14)
    try:
        e.position(FEN)
        r = e.search(f"go depth {depth}", 900)
        lines = [x for x in e.since(0) if x.startswith("info depth") and " multipv " in x]
    finally:
        e.close()
    # take the LAST line for each multipv index (deepest)
    per = {}
    for ln in lines:
        m_idx = re.search(r"multipv (\d+)", ln)
        m_sc = re.search(r"score (cp|mate) (-?\d+)", ln)
        m_pv = re.search(r" pv (\S+)", ln)
        if not (m_idx and m_sc and m_pv):
            continue
        per[int(m_idx.group(1))] = (m_pv.group(1), m_sc.group(1), int(m_sc.group(2)))
    return per, r


def score_restricted(move, depth=16):
    e = Engine(PC, opts=S14)
    try:
        e.position(FEN)
        r = e.search(f"go depth {depth} searchmoves {move}", 900)
    finally:
        e.close()
    return r["score"], r["nodes"], r["bestmove"]


print("== A. MultiPV 4, Hash 16, depth 16 — each root move's own score from one search")
per, rr = score_moves_multipv(4)
mv_scores = {}
for idx in sorted(per):
    mv, kind, val = per[idx]
    mv_scores[mv] = f"{kind} {val}"
    print(f"  multipv {idx}: {mv:6s} score {kind} {val}")
print(f"  (final bestmove {rr['bestmove']}, nodes {rr['nodes']})")
print()

print("== B. each move restricted, MultiPV 1, Hash 16, depth 16 (cross-check; restrictions perturb a few cp)")
restricted = {}
for m in MOVES:
    sc, nodes, bm = score_restricted(m)
    restricted[m] = sc
    print(f"  searchmoves {m}: {sc:9s} nodes {nodes:8d}  (bestmove {bm})")
print()

print("== verdict")
healthy = mv_scores.get("g7g6")
perturb = None
if healthy and restricted.get("g7g6") and healthy.split()[0] == restricted["g7g6"].split()[0]:
    perturb = abs(int(healthy.split()[1]) - int(restricted["g7g6"].split()[1]))
print(f"  healthy move g7g6: MultiPV score {healthy}, restricted score {restricted.get('g7g6')}, "
      f"restriction perturbation = {perturb} cp")
for m in ("f6d7", "b8a8"):
    a, b = mv_scores.get(m), restricted.get(m)
    d = None
    if a and b and a.split()[0] == b.split()[0]:
        d = int(b.split()[1]) - int(healthy.split()[1]) if healthy else None
    print(f"  {m}: MultiPV score {a}, restricted score {b}, "
          f"difference vs g7g6 (restricted) = {d} cp" if d is not None else f"  {m}: {a} / {b}")

res = {"fen": FEN, "multipv": {k: v for k, v in mv_scores.items()}, "restricted": restricted,
       "perturbation_cp": perturb}
with open(os.path.join(OUT, "three_moves.json"), "w") as f:
    json.dump(res, f, indent=1)
print("\nwrote three_moves.json")
