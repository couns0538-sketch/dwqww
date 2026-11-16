#!/usr/bin/env python3
"""perft5_pc20.py EXE BUILD — perft 5 on smaller G positions vs python-chess, PC20, Threads 1."""
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
# pick the sparse ones (fewest pieces) so perft 5 is affordable
fens.sort(key=lambda f: len(chess.Board(f).piece_map()))
def perft(fen,d=5):
    e=Engine(EXE,options=PC20_LINES,timeout=600); e.start()
    try:
        _,r=e.position(fen=fen)
        if r: return None
        e.send(f"go perft {d}"); lines=e.read_until("nodes ",timeout=400)
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
print(f"build {BUILD}  PC20, Threads 1 — perft 5 on the 4 sparsest G positions\n")
bad=0
for fen in fens[:4]:
    b=chess.Board(fen)
    eng=perft(fen); py=pyperft(b,5)
    ok=eng==py
    if not ok: bad+=1
    print(f"  pieces {len(b.piece_map()):2} engine {str(eng):>10} py {py:>10} {'MATCH' if ok else 'MISMATCH'}  {fen[:40]}")
print(f"\n  mismatches: {bad}")
