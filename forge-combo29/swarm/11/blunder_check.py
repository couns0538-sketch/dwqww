#!/usr/bin/env python3
"""blunder_check.py EXE BUILD — at match budgets, does the engine's move hold up one ply later?
For each position, play the chosen move, then search the reply at the SAME budget and see whether the
score collapses (a gross blunder indicator). PC20, Threads 1."""
import os,re,sys
sys.path.insert(0,'/agent/repos/dwqww/forge-combo29/swarm/11')
import chess
from ucio import Engine
from pc20 import PC20_LINES
EXE=sys.argv[1]; BUILD=sys.argv[2] if len(sys.argv)>2 else "?"
fens=[]
with open("positions/G_set_G.epd") as f:
    for line in f:
        line=line.strip()
        if not line or line.startswith("#"): continue
        x=line.split(";")[0].strip().split(" ")[:6]
        if len(x)==6: fens.append(" ".join(x))
        if len(fens)>=10: break
def search(fen,N=20000):
    e=Engine(EXE,options=PC20_LINES,timeout=300); e.start()
    try:
        _,r=e.position(fen=fen)
        if r: return None
        infos,bm,_=e.go(f"go nodes {N}")
        sc=None
        for l in infos:
            m=re.search(r"score (cp|mate) (-?\d+)",l)
            if m: sc=(m.group(1),int(m.group(2)))
        return bm,sc
    finally: e.quit()
print(f"build {BUILD}  PC20, Threads 1, go nodes 20000\n{'position':34} {'own score':>12} {'after reply':>12} {'delta':>8}")
worst=0
for fen in fens:
    r=search(fen)
    if r is None: continue
    bm,sc=r
    b=chess.Board(fen)
    try: mv=chess.Move.from_uci(bm)
    except Exception: continue
    if mv not in b.legal_moves: continue
    b.push(mv)
    r2=search(b.fen())
    if r2 is None: continue
    if sc and r2[1] and sc[0]=="cp" and r2[1][0]=="cp":
        # score after our move is from the opponent's view, so negate
        delta = -r2[1][1] - sc[1]
        worst=max(worst,abs(delta))
        print(f"{fen[:32]:34} {str(sc):>12} {str(r2[1]):>12} {delta:>8}")
print(f"\n  largest score swing one ply later: {worst} cp (a gross blunder would be several hundred)")
