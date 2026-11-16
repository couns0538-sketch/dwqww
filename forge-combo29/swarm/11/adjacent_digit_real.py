#!/usr/bin/env python3
"""adjacent_digit_real.py EXE BUILD — the adjacent-digit FEN class (S-F2) on real positions.
Takes real G positions, rewrites ONE rank's empty run as two adjacent digits (same board),
and checks the search answer is identical. If identical, the class is purely cosmetic."""
import os,re,sys
sys.path.insert(0,'/agent/repos/dwqww/forge-combo29/swarm/11')
import chess
from ucio import Engine
from pc20 import PC20_LINES
EXE=sys.argv[1]; BUILD=sys.argv[2] if len(sys.argv)>2 else "?"
def split_rank(rank):
    """'8' -> '44' ; '5K2' -> '5K11' style splitting of a numeric run into two parts."""
    out=[]
    for ch in rank:
        if ch.isdigit() and int(ch)>=2:
            a=int(ch)//2; b=int(ch)-a
            out.append(str(a)+str(b))
        else:
            out.append(ch)
    return "".join(out)
def variant(fen):
    f=fen.split(" ")
    ranks=f[0].split("/")
    for i,r in enumerate(ranks):
        if any(c.isdigit() and int(c)>=2 for c in r):
            ranks[i]=split_rank(r); break
    f[0]="/".join(ranks)
    return " ".join(f)
fens=[]
with open("positions/G_set_G.epd") as f:
    for line in f:
        line=line.strip()
        if not line or line.startswith("#"): continue
        x=line.split(";")[0].strip().split(" ")[:6]
        if len(x)==6: fens.append(" ".join(x))
        if len(fens)>=25: break
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
print(f"build {BUILD}  PC20, Threads 1\n")
tested=same=diff=refused=0
for fen in fens:
    v=variant(fen)
    if v==fen: continue
    try:
        a=chess.Board(fen); b=chess.Board(v)
        if a.board_fen()!=b.board_fen():
            print(f"  SKIP (my rewrite changed the board): {v[:50]}"); continue
    except Exception:
        pass
    c=run(fen,"go softnodes 2000"); j=run(v,"go softnodes 2000")
    if c[0]=="REFUSED" or j[0]=="REFUSED": refused+=1; continue
    tested+=1
    if c==j: same+=1
    else: diff+=1; print(f"  DIFF clean={c} adj={j}  {v[:56]}")
print(f"  tested {tested}: identical {same}, different {diff}, refused {refused}")
