#!/usr/bin/env python3
"""verify_pc_mate8.py — seat 20 job 46: is the PC build's `mate 8` at halfmove 85 REAL, and does the base find it
at a higher depth?

The observation (job44): on `1K6/8/8/3R4/8/8/8/k7 w` at halfmove 85, `go depth 10`:
    base 6b98f217 + S14 -> cp 349
    PC r15 + PC20       -> mate 8        <- a mate the base does not see at that depth

Three questions, each answered by measurement, Threads 1 throughout:
  Q1 is the PC's mate real? Replay the PC's own PV and require it to end in checkmate.
  Q2 does the base find the same mate at a higher depth? Sweep depth and record the first depth at which it says mate.
  Q3 is the mate distance consistent? `mate 8` needs 15 plies; the same board at counter 0 measured `mate 8` too,
     so the two should agree.

Controls:
  * the PV replay is the control for "is it a mate" — if the PV does not end in mate, the claim fails, not passes;
  * a counter-0 run on both builds must report the same mate distance (independence from the counter).

usage: verify_pc_mate8.py <base-exe> <pc-exe> <outdir>
"""
import json
import os
import re
import sys

import chess

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "AUDIT"))
from hardened import Engine  # noqa: E402

BASE, PC, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
os.makedirs(OUT, exist_ok=True)

S14 = [("Threads", 1), ("Hash", 16), ("LmrQuietBase", 93), ("LmrQuietDivisor", 205), ("LmrNoisyBase", 13),
       ("LmrNoisyDivisor", 333), ("LmrHistoryDivisor", 5643), ("NullMoveBase", 5), ("LmpBase", 8),
       ("HistoryPruneMultiplier", 2220), ("HistoryBonusQuadratic", 24), ("HistoryBonusLinear", 54),
       ("HistoryBonusMax", 2212), ("SingularDepth", 6), ("IirDepth", 2), ("NonPawnCorrection", "true"),
       ("OwnBook", "false")]
PC20 = S14 + [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"), ("CorrHistV2", "true"),
              ("MateAlphaGuard", "true")]
KRK = "1K6/8/8/3R4/8/8/8/k7 w - - {hm} 1"


def run(exe, opts, fen, go):
    e = Engine(exe, opts=list(opts))
    try:
        e.position(fen)
        r = e.search(go, 600)
    finally:
        e.close()
    return r


def replay(fen, pv):
    """play the PV with python-chess; return (all_legal, plies_played, ends_in_mate, final_fen)."""
    b = chess.Board(fen)
    played = 0
    for mv in pv:
        try:
            m = chess.Move.from_uci(mv)
        except ValueError:
            return False, played, False, b.fen()
        if m not in b.legal_moves:
            return False, played, False, b.fen()
        b.push(m)
        played += 1
    return True, played, b.is_checkmate(), b.fen()


rows = []
print("=== Q1: the PC build's depth-10 answer at halfmove 85, PV replayed")
r85 = run(PC, PC20, KRK.format(hm=85), "go depth 10")
legal, played, mate, fen_after = replay(KRK.format(hm=85), r85["pv"])
print(f"  score {r85['score']}   pv {len(r85['pv'])} plies   nodes {r85['nodes']}")
print(f"  PV: {' '.join(r85['pv'])}")
print(f"  replay: all legal {legal}, played {played}, ENDS IN CHECKMATE: {mate}")
print(f"  final: {fen_after}")
rows.append({"q": "Q1", "build": "pc20", "halfmove": 85, "score": r85["score"],
             "pv": r85["pv"], "pv_all_legal": legal, "pv_plies": played,
             "pv_ends_in_checkmate": mate, "final_fen": fen_after})

if r85["score"] and r85["score"].startswith("mate"):
    claim = int(r85["score"].split()[1])
    need = 2 * claim - 1
    print(f"  claimed mate {claim} needs {need} plies; PV has {len(r85['pv'])} -> "
          f"{'FULL LENGTH' if len(r85['pv']) >= need else 'TRUNCATED'}")

print()
print("=== Q2: does the BASE build find a mate at a higher depth on the same board?")
base_first_mate = None
for d in (10, 12, 14, 16, 18, 20, 24):
    r = run(BASE, S14, KRK.format(hm=85), f"go depth {d}")
    ok, pl, mt, _fa = replay(KRK.format(hm=85), r["pv"])
    tag = ""
    if r["score"] and r["score"].startswith("mate"):
        tag = f"  <- MATE, pv ends in mate: {mt}"
        if base_first_mate is None:
            base_first_mate = d
    print(f"  base depth {d:2d}: {str(r['score']):9s} pv {len(r['pv']):2d} nodes {r['nodes']:9d} "
          f"pv_ends_in_mate {mt}{tag}")
    rows.append({"q": "Q2", "build": "base_s14", "halfmove": 85, "depth": d, "score": r["score"],
                 "pv_plies": len(r["pv"]), "pv_ends_in_checkmate": mt, "nodes": r["nodes"]})
print(f"  base first reports a mate at depth: {base_first_mate}")

print()
print("=== Q2b: and on the PC build, for the same depth sweep (when does it first see the mate?)")
pc_first_mate = None
for d in (8, 9, 10, 11, 12, 14):
    r = run(PC, PC20, KRK.format(hm=85), f"go depth {d}")
    ok, pl, mt, _fa = replay(KRK.format(hm=85), r["pv"])
    if r["score"] and r["score"].startswith("mate") and pc_first_mate is None:
        pc_first_mate = d
    print(f"  pc   depth {d:2d}: {str(r['score']):9s} pv {len(r['pv']):2d} nodes {r['nodes']:9d} "
          f"pv_ends_in_mate {mt}")
    rows.append({"q": "Q2b", "build": "pc20", "halfmove": 85, "depth": d, "score": r["score"],
                 "pv_plies": len(r["pv"]), "pv_ends_in_checkmate": mt, "nodes": r["nodes"]})
print(f"  pc first reports a mate at depth: {pc_first_mate}")

print()
print("=== Q3: independence from the counter (counter 0, same board, both builds, depth 20)")
for label, exe, opts in (("base_s14", BASE, S14), ("pc20", PC, PC20)):
    r = run(exe, opts, KRK.format(hm=0), "go depth 20")
    ok, pl, mt, _fa = replay(KRK.format(hm=0), r["pv"])
    print(f"  {label:9s} {str(r['score']):9s} pv {len(r['pv']):2d} pv_ends_in_mate {mt}")
    rows.append({"q": "Q3", "build": label, "halfmove": 0, "depth": 20, "score": r["score"],
                 "pv_plies": len(r["pv"]), "pv_ends_in_checkmate": mt})

with open(os.path.join(OUT, "verify_pc_mate8.json"), "w") as f:
    json.dump({"board": KRK, "rows": rows}, f, indent=1)
print("\nwrote verify_pc_mate8.json")
