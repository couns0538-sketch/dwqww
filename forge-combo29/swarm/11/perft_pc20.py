#!/usr/bin/env python3
"""perft_pc20.py EXE BUILD — perft 1..4 on real G positions vs python-chess, PC20, Threads 1.
The strongest single move-generation check: any generation bug shows up here."""
import os,re,sys,random
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
def perft(fen,d):
    e=Engine(EXE,options=PC20_LINES,timeout=600); e.start()
    try:
        _,r=e.position(fen=fen)
        if r: return None
        e.send(f"go perft {d}"); lines=e.read_until("nodes ",timeout=300)
        for l in lines:
            m=re.match(r"nodes (\d+)",l)
            if m: return int(m.group(1))
        return None
    finally: e.quit()
def pyperft(b,d):
    if d==0: return 1
    s=0
    for m in b.legal_moves:
        b.push(m); s+=pyperft(b,d-1); b.pop()
    return s
print(f"build {BUILD}  PC20, Threads 1 — perft 1..4 on {len(fens)} G positions\n")
bad=0
for fen in fens:
    b=chess.Board(fen)
    row=[]
    for d in (1,2,3,4):
        eng=perft(fen,d)
        py=pyperft(b,d)
        ok = eng==py
        if not ok: bad+=1
        row.append(f"d{d}:{eng}{'=' if ok else '!='}{py}")
    print(f"  {fen[:44]:46} {' '.join(row)}")
print(f"\n  mismatches: {bad}")
