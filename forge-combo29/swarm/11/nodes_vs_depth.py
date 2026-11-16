#!/usr/bin/env python3
"""nodes_vs_depth.py EXE BUILD — does the node undershoot cost SEARCH QUALITY?
Compares `go nodes 50000` against the depth it actually completes, versus going one depth deeper.
If the answer differs, the undershoot is costing the engine a depth."""
import os,re,sys
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
        if len(fens)>=20: break
def run(fen,go):
    e=Engine(EXE,options=PC20_LINES,timeout=300); e.start()
    try:
        _,r=e.position(fen=fen)
        if r: return None
        infos,bm,_=e.go(go)
        d=n=s=None
        for l in infos:
            md=re.search(r"depth (\d+)",l); mn=re.search(r"nodes (\d+)",l); ms=re.search(r"score (cp|mate) (-?\d+)",l)
            if md: d=int(md.group(1))
            if mn: n=int(mn.group(1))
            if ms: s=ms.groups()
        return (bm,d,n,s)
    finally: e.quit()
print(f"build {BUILD}  PC20, Threads 1, {len(fens)} G positions")
print("  for each: what `go nodes 50000` gave, then what the NEXT depth gives\n")
samebm=diffbm=0
for fen in fens[:12]:
    a=run(fen,"go nodes 50000")
    if a is None: continue
    bm,d,n,s=a
    b=run(fen,f"go depth {d+1}")
    if b is None: continue
    ch = bm!=b[0]
    samebm += (not ch); diffbm += ch
    print(f"  nodes50k: bm={bm} d={d} n={n} | depth {d+1}: bm={b[0]} d={b[1]} n={b[2]} {'MOVE CHANGES' if ch else 'same move'}")
print(f"\n  at the completed depth the move is the SAME as one deeper: {samebm}, CHANGES: {diffbm}")
