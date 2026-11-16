#!/usr/bin/env python3
"""cuckoo_effect.py EXE — CuckooRep only fires when an upcoming repetition exists.
So test it where repetitions exist: positions reached by repeating moves, vs their
non-repeating twins. A switch that is truly active must change THESE searches."""
import os,sys,re
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from ucio import Engine
from pc20 import PC20_LINES
S14=PC20_LINES[:14]
BASE=S14+["setoption name Threads value 1","setoption name Hash value 16","setoption name OwnBook value false"]
PLUS=BASE+["setoption name CuckooRep value true"]
MOVES=["g1f3 g8f6 f3g1 f6g8",                                  # 2nd occurrence of start
       "g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8",              # 3rd occurrence
       "e2e4 e7e5 g1f3 b8c6 f1c4 g8f6 f3g5 d7d5 e4d5 f6d5 g5f3",# a normal game
       "d2d4 d7d5 c2c4 e7e6 b1c3 g8f6 c4d5 e6d5"]
def run(moves,opts):
    e=Engine(EXE:=sys.argv[1],options=opts,timeout=300); e.start()
    try:
        e.send("position startpos moves "+moves); e.send("isready"); e.read_until("readyok")
        infos,bm,_=e.go("go depth 10")
        nodes=None
        for l in infos:
            m=re.search(r"nodes (\d+)",l)
            if m: nodes=int(m.group(1))
        return bm,nodes
    finally: e.quit()
print(f"exe {sys.argv[1]}\nS14 vs S14+CuckooRep, depth 10, Threads 1\n")
print(f"{'moves':56} {'base':>16} {'+Cuckoo':>16} changed")
for mv in MOVES:
    b=run(mv,BASE); p=run(mv,PLUS)
    print(f"{mv[:54]:56} {str(b):>16} {str(p):>16} {b!=p}")
