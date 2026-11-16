#!/usr/bin/env python3
"""matealpha_effect.py EXE — is MateAlphaGuard observable? (the option that needs the build flag)
Compare PC20 with MateAlphaGuard true vs false at depth 12, Threads 1, on 30 G positions.
A switch that never changes anything is worth reporting as inert."""
import os,re,sys
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from ucio import Engine
from pc20 import PC20_LINES
ON  = list(PC20_LINES)
OFF = [l.replace("MateAlphaGuard value true","MateAlphaGuard value false") for l in PC20_LINES]
G="positions/G_set_G.epd"
def run(fen,opts,depth=12):
    e=Engine(sys.argv[1],options=opts,timeout=300); e.start()
    try:
        _,r=e.position(fen=fen)
        if r: return None
        infos,bm,_=e.go(f"go depth {depth}")
        nodes=None; score=None
        for l in infos:
            m=re.search(r"nodes (\d+)",l)
            if m: nodes=int(m.group(1))
            m2=re.search(r"score (cp|mate) (-?\d+)",l)
            if m2: score=(m2.group(1),int(m2.group(2)))
        return (bm,nodes,score)
    finally: e.quit()
fens=[]
with open(G) as f:
    for line in f:
        line=line.strip()
        if not line or line.startswith("#"): continue
        x=line.split(";")[0].strip().split(" ")[:6]
        if len(x)==6: fens.append(" ".join(x))
        if len(fens)>=30: break
print(f"exe {sys.argv[1]}\nMateAlphaGuard true vs false, PC20 otherwise, depth 12, Threads 1, {len(fens)} G positions\n")
mc=nc=sc=same=0
for fen in fens:
    a=run(fen,ON); b=run(fen,OFF)
    if a is None or b is None: continue
    if a[0]!=b[0]: mc+=1
    if a[1]!=b[1]: nc+=1
    if a[2]!=b[2]: sc+=1
    if a==b: same+=1
print(f"  bestmove changed {mc}, nodes changed {nc}, score changed {sc}, fully identical {same}")
