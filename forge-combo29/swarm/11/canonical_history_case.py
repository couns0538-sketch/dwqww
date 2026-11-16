#!/usr/bin/env python3
"""canonical_history_case.py EXE BUILD — proves the canonical history case is STABLE, not noise.
Same board, FEN form vs third-occurrence-by-move-list, 5 runs each in fresh processes.
If both are stable and differ, history-alone is established without relying on anyone's openings."""
import sys,re
sys.path.insert(0,'/agent/repos/dwqww/forge-combo29/swarm/11')
import chess
from ucio import Engine
from pc20 import PC20_LINES
EXE=sys.argv[1]; BUILD=sys.argv[2] if len(sys.argv)>2 else "?"
FEN="r1bqkb1r/pp2pppp/2n2n2/2pp4/3P1B2/4PN2/PPP2PPP/RN1QKB1R w KQkq - 1 5"
PATH="d2d4 g8f6 g1f3 d7d5 c1f4 c7c5 e2e3 b8c6"
CYCLE="f3g1 c6b8 g1f3 b8c6"
def run(fen=None, moves=None):
    e=Engine(EXE,options=PC20_LINES,timeout=180); e.start()
    try:
        if moves is not None:
            e.send("position startpos moves "+moves); e.send("isready")
        else:
            e.send("position fen "+fen); e.send("isready")
        if [l for l in e.read_until("readyok") if "invalid" in l or "illegal" in l]:
            return None
        infos,bm,_=e.go("go softnodes 2000",timeout=60)
        n=0
        for l in infos:
            m=re.search(r"nodes (\d+)",l)
            if m: n=int(m.group(1))
        return (bm,n)
    finally: e.quit()
# verify the board reached by the cycle equals FEN's board
b=chess.Board()
for m in PATH.split(): b.push(chess.Move.from_uci(m))
b1=b.fen()
for m in CYCLE.split(): b.push(chess.Move.from_uci(m))
b2=b.fen()
print(f"build {BUILD}  PC20, Threads 1, softnodes 2000")
print(f"  boards identical after the cycle: {b1==b2}")
print(f"  board: {b1}\n")
a=[run(fen=FEN) for _ in range(5)]
c=[run(moves=PATH+" "+CYCLE) for _ in range(5)]
print(f"  FEN form, 5 runs          : {a}")
print(f"  third occurrence, 5 runs  : {c}")
sa=len(set(a))==1; sc=len(set(c))==1
print(f"\n  FEN stable {sa}, occurrence stable {sc}, differ {a[0]!=c[0]}")
if sa and sc and a[0]!=c[0]:
    print(f"  => CANONICAL: {a[0][0]} in {a[0][1]} nodes (FEN) vs {c[0][1]} nodes (history). Stable, not noise.")
