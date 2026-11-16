#!/usr/bin/env python3
"""score_progression.py EXE BUILD — as the node budget grows, does the score settle (not oscillate
wildly) and does the move converge? Sanity check of the match path at 20k/50k/250k."""
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
        if len(fens)>=8: break
def run(fen,N):
    e=Engine(EXE,options=PC20_LINES,timeout=300); e.start()
    try:
        _,r=e.position(fen=fen)
        if r: return None
        infos,bm,_=e.go(f"go nodes {N}")
        sc=None; d=None
        for l in infos:
            m=re.search(r"score (cp|mate) (-?\d+)",l)
            if m: sc=(m.group(1),int(m.group(2)))
            md=re.search(r"depth (\d+)",l)
            if md: d=int(md.group(1))
        return (bm,d,sc)
    finally: e.quit()
print(f"build {BUILD}  PC20, Threads 1\n{'position':40} {'20k':>22} {'50k':>22} {'250k':>22}")
for fen in fens:
    row=[]
    for N in (20000,50000,250000):
        r=run(fen,N)
        row.append("FAIL" if r is None else f"{r[0]} d{r[1]} {r[2][0]}{r[2][1]}")
    print(f"{fen[:38]:40} {row[0]:>22} {row[1]:>22} {row[2]:>22}")
