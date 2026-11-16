#!/usr/bin/env python3
"""fen_vs_moves.py EXE BUILD — does `position fen <X>` give the same search as
`position startpos moves <path to X>`? A GUI may use either form; if they differ the engine
is not position-consistent. PC20, Threads 1."""
import os,re,sys
sys.path.insert(0,'/agent/repos/dwqww/forge-combo29/swarm/11')
import chess
from ucio import Engine
from pc20 import PC20_LINES
EXE=sys.argv[1]; BUILD=sys.argv[2] if len(sys.argv)>2 else "?"
SEQS=["e2e4 e7e5 g1f3 b8c6 f1c4 f8c5 d2d3 g8f6",
      "d2d4 d7d5 c2c4 e7e6 b1c3 g8f6",
      "e2e4 c7c5 g1f3 d7d6 d2d4 c5d4",
      "e2e4 e7e6 d2d4 d7d5 e4e5 c7c5",
      "c2c4 e7e5 b1c3 g8f6 g2g3 d7d5",
      "e2e4 d7d5 e4d5 d8d5 b1c3 d5a5",
      "d2d4 g8f6 c2c4 g7g6 b1c3 f8g7",
      "e2e4 e7e5 g1f3 b8c6 f1b5 a7a6"]
def run_fen(fen):
    e=Engine(EXE,options=PC20_LINES,timeout=300); e.start()
    try:
        _,r=e.position(fen=fen)
        if r: return ("REFUSED",)
        infos,bm,_=e.go("go softnodes 2000")
        n=None
        for l in infos:
            m=re.search(r"nodes (\d+)",l)
            if m: n=int(m.group(1))
        return (bm,n)
    finally: e.quit()
def run_moves(mv):
    e=Engine(EXE,options=PC20_LINES,timeout=300); e.start()
    try:
        e.send("position startpos moves "+mv); e.send("isready")
        if [l for l in e.read_until("readyok") if "invalid" in l or "illegal" in l]: return ("REFUSED",)
        infos,bm,_=e.go("go softnodes 2000")
        n=None
        for l in infos:
            m=re.search(r"nodes (\d+)",l)
            if m: n=int(m.group(1))
        return (bm,n)
    finally: e.quit()
print(f"build {BUILD}  PC20, Threads 1\n{'position':52} {'via fen':>16} {'via moves':>16} same")
same=diff=0
for mv in SEQS:
    b=chess.Board()
    for m in mv.split(): b.push(chess.Move.from_uci(m))
    fen=b.fen()
    a=run_fen(fen); c=run_moves(mv)
    eq = a==c
    same+=eq; diff+= (not eq)
    print(f"{mv[:50]:52} {str(a):>16} {str(c):>16} {'yes' if eq else 'NO'}")
print(f"\n  same {same}, different {diff}")
