#!/usr/bin/env python3
"""Rule-1 control for the mate check: a zero needs a planted one.

The zero I report is "0 positive mate claims failed to be delivered by their own PV, and 0 distances
disagreed with python-chess". That counts only if the SAME check flags a planted failure.

Each row below states: what the value under test is, whether the check UNDER TEST passes or fails it,
and whether it SHOULD pass. A correct control means "check result" == "should pass".
"""
import json, sys
import chess

def pv_mates_in(fen, pv):
    """The check under test: at which ply does this PV deliver mate (None if never)."""
    if not pv: return None
    b=chess.Board(fen)
    for i,u in enumerate(pv,1):
        try: m=chess.Move.from_uci(u)
        except ValueError: return None
        if m not in b.legal_moves: return None
        b.push(m)
        if b.is_checkmate(): return i
    return None

def claim_is_delivered(fen, pv, claim):
    """The real assertion: a claim of mate M must be delivered within 2M-1 plies."""
    d=pv_mates_in(fen,pv)
    if claim is None or claim<=0: return None
    return d is not None and d <= 2*claim-1

pos=json.load(open("out/positions.json"))
mate2=[p for p in pos if p["true_mate_plies"]==3][0]
fen=mate2["fen"]
rows=json.load(open("out/mates.json"))["rows"]
real=[r for r in rows if r["fen"]==fen and r["N"]==250000][0]
pv=real["pv"]
print("control position:", fen, "(python-chess: forced mate in 3 plies)")
print("engine PV:", " ".join(pv), "-> PV delivers mate at ply", pv_mates_in(fen,pv))
print("engine claimed mate", real["mate"], "-> needs <=", 2*real["mate"]-1, "plies")
print()

cases=[]
# P0: the real claim against the real PV must PASS
cases.append(("P0 real claim","claim mate 2, real PV delivers at ply 3", claim_is_delivered(fen,pv,2), True))
# A: an over-optimistic claim of mate 1 cannot be delivered within 1 ply
cases.append(("A claim too short","claim mate 1 (needs <=1), PV needs 3", claim_is_delivered(fen,pv,1), False))
# B: a truncated PV never delivers mate
cases.append(("B truncated PV","claim mate 2, PV cut to 1 ply", claim_is_delivered(fen,pv[:1],2), False))
# C: a PV containing an illegal move is rejected outright
bad=list(pv); bad[0]="a1a8"
cases.append(("C illegal PV move","claim mate 2, first PV move illegal", claim_is_delivered(fen,bad,2), False))
# D: an empty PV
cases.append(("D empty PV","claim mate 2, no PV at all", claim_is_delivered(fen,[],2), False))

ok=True
print("| plant | what it is | check says delivered? | should be delivered? | result |")
print("|---|---|---|---|---|")
for name,desc,got,want in cases:
    good = (got==want)
    ok &= good
    print("| %s | %s | %s | %s | %s |"%(name,desc,got,want,"correct" if good else "WRONG"))
print()
print("Rule 1 verdict:",
      "every planted mate failure is rejected and the real claim is accepted, so the zero is a measurement"
      if ok else "FAILED - the zero would be 'not shown'")
sys.exit(0 if ok else 1)
