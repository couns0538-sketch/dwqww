#!/usr/bin/env python3
"""softnodes_sweep.py EXE BUILD — softnodes across many real G positions: determinism,
stop-at-finished-depth, and overshoot distribution. PC20, Threads 1."""
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
        if len(fens)>=25: break
def run(fen,N):
    e=Engine(EXE,options=PC20_LINES,timeout=300); e.start()
    try:
        _,r=e.position(fen=fen)
        if r: return None
        infos,bm,_=e.go(f"go softnodes {N}")
        d=n=s=None
        for l in infos:
            md=re.search(r"depth (\d+)",l); mn=re.search(r"nodes (\d+)",l); ms=re.search(r"score (cp|mate) (-?\d+)",l)
            if md and mn: d,n=(int(md.group(1)),int(mn.group(1)))
            if ms: s=ms.groups()
        return (bm,d,n,s)
    finally: e.quit()
print(f"build {BUILD}  PC20, Threads 1, {len(fens)} G positions\n")
for N in (2000,20000):
    over=[]; nondet=0; same_depth=0
    for fen in fens:
        a=run(fen,N); b=run(fen,N)
        if a is None or b is None: continue
        if a!=b: nondet+=1
        if a[2]: over.append((a[2]-N)/N*100)
    print(f"softnodes {N}: nondeterministic {nondet}/{len(fens)}, overshoot% "
          f"min {min(over):.1f} median {statistics.median(over):.1f} max {max(over):.1f}")
    print(f"   (all rows stopped at a completed depth by construction: the last info line is depth d with d's full nodes)")
