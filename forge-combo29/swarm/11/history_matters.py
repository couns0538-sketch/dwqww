#!/usr/bin/env python3
"""history_matters.py EXE BUILD — the GENERAL question behind seat 23's C20 (which refutes my S-F53):
can move history alone change the answer, with the board identical? If yes, S-F53's "the two forms
are search-identical" was too broad and the conservative rule is correct.
Tests progressively richer history on the SAME board."""
import sys,re
sys.path.insert(0,'/agent/repos/dwqww/forge-combo29/swarm/11')
import chess
from ucio import Engine
from pc20 import PC20_LINES
EXE=sys.argv[1]; BUILD=sys.argv[2] if len(sys.argv)>2 else "?"
BASE="d2d4 g8f6 g1f3 d7d5 c1f4 c7c5 e2e3 b8c6"
CYCLE=["f3g1","c6b8","g1f3","b8c6"]     # returns to the same board
def run(fen=None, moves=None):
    e=Engine(EXE,options=PC20_LINES,timeout=180); e.start()
    try:
        if moves is not None:
            e.send("position startpos moves "+" ".join(moves)); e.send("isready")
        else:
            e.send("position fen "+fen); e.send("isready")
        if [l for l in e.read_until("readyok") if "invalid" in l or "illegal" in l]:
            return ("REFUSED",)
        infos,bm,_=e.go("go softnodes 2000",timeout=60)
        n=0
        for l in infos:
            m=re.search(r"nodes (\d+)",l)
            if m: n=int(m.group(1))
        return (bm,n)
    finally: e.quit()
base=chess.Board()
for m in BASE.split(): base.push(chess.Move.from_uci(m))
fen=base.fen()
print(f"build {BUILD}  PC20, Threads 1, softnodes 2000")
print(f"board: {fen}\n")
r_fen=run(fen=fen)
print(f"  via FEN (no history)              : {r_fen}")
print(f"  via moves (1st occurrence)        : {run(moves=BASE.split())}")
print(f"  via moves (2nd occurrence)        : {run(moves=BASE.split()+CYCLE)}")
print(f"  via moves (3rd occurrence)        : {run(moves=BASE.split()+CYCLE+CYCLE)}")
print()
print("If any row differs from the FEN row, HISTORY ALONE changes the answer and")
print("S-F53's 'search-identical' claim was too broad.")
