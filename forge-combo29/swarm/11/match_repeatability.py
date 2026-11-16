#!/usr/bin/env python3
"""match_repeatability.py EXE BUILD — at the match node budgets, is the MOVE stable run to run
(Threads 1)? A match needs reproducible decisions."""
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
        if len(fens)>=12: break
def run(fen,N):
    e=Engine(EXE,options=PC20_LINES,timeout=300); e.start()
    try:
        _,r=e.position(fen=fen)
        if r: return None
        infos,bm,_=e.go(f"go nodes {N}")
        n=None; sc=None
        for l in infos:
            m=re.search(r"nodes (\d+)",l)
            if m: n=int(m.group(1))
            ms=re.search(r"score (cp|mate) (-?\d+)",l)
            if ms: sc=ms.groups()
        return (bm,n,sc)
    finally: e.quit()
print(f"build {BUILD}  PC20, Threads 1, {len(fens)} G positions\n")
for N in (20000,50000,250000):
    unstable=0; details=[]
    for fen in fens:
        a=run(fen,N); b=run(fen,N)
        if a is None or b is None: continue
        if a[0]!=b[0]: unstable+=1; details.append((fen[:34],a,b))
    print(f"  go nodes {N:6}: unstable {unstable}/{len(fens)}")
    for d in details[:2]: print(f"     {d}")
