#!/usr/bin/env python3
"""extra_token_real.py EXE BUILD — does the silently-accepted extra token EVER change the board
in a way that matters? Compares full move sequences with and without a trailing junk token,
across real G positions, under the PC's real search modes."""
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
        if len(fens)>=30: break
def run(fen,go):
    e=Engine(EXE,options=PC20_LINES,timeout=300); e.start()
    try:
        _,r=e.position(fen=fen)
        if r: return ("REFUSED",)
        infos,bm,_=e.go(go)
        n=None
        for l in infos:
            m=re.search(r"nodes (\d+)",l)
            if m: n=int(m.group(1))
        return (bm,n)
    finally: e.quit()
print(f"build {BUILD}  PC20, Threads 1  {len(fens)} real G positions")
for go in ("go softnodes 2000","go nodes 20000"):
    same=diff=0; ex=[]
    for fen in fens:
        clean=run(fen,go); junk=run(fen+" zzz",go)
        if clean[0]=="REFUSED" or junk[0]=="REFUSED": continue
        if clean==junk: same+=1
        else: diff+=1; ex.append((fen[:40],clean,junk))
    print(f"  {go:18} identical {same}, different {diff}")
    for e in ex[:3]: print(f"     {e}")
