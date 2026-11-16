#!/usr/bin/env python3
"""nodes_real.py EXE BUILD — the owner's MATCH settings: go nodes 20000/50000/250000.
PC20, Threads 1. Are they deterministic, and how far past N do they go (like softnodes)?"""
import os,re,sys,statistics
sys.path.insert(0,'/agent/repos/dwqww/forge-combo29/swarm/11')
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
        if len(fens)>=15: break
def run(fen,N):
    e=Engine(EXE,options=PC20_LINES,timeout=300); e.start()
    try:
        _,r=e.position(fen=fen)
        if r: return None
        infos,bm,_=e.go(f"go nodes {N}")
        n=d=None
        for l in infos:
            md=re.search(r"depth (\d+)",l); mn=re.search(r"nodes (\d+)",l)
            if md: d=int(md.group(1))
            if mn: n=int(mn.group(1))
        return (bm,n,d)
    finally: e.quit()
print(f"build {BUILD}  PC20, Threads 1, {len(fens)} G positions\n")
for N in (20000,50000,250000):
    nondet=0; over=[]
    for fen in fens:
        a=run(fen,N); b=run(fen,N)
        if a is None or b is None: continue
        if a!=b: nondet+=1
        if a[1]: over.append((a[1]-N)/N*100)
    if over:
        print(f"go nodes {N:6}: nondeterministic {nondet}/{len(fens)}, overrun% min {min(over):.1f} "
              f"median {statistics.median(over):.2f} max {max(over):.2f}")
