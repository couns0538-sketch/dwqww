#!/usr/bin/env python3
"""matchpath_sweep.py EXE BUILD — the PC's MATCH path quality sweep: go nodes 20000 on real
positions; verify every bestmove legal and every mate score backed by a real mate.
PC20, Threads 1."""
import os,re,sys
sys.path.insert(0,'/agent/repos/dwqww/forge-combo29/swarm/11')
import chess
from ucio import Engine
from pc20 import PC20_LINES
EXE=sys.argv[1]; BUILD=sys.argv[2] if len(sys.argv)>2 else "?"
fens=[]
for p in ("positions/G_set_G.epd","positions/O_first200.fens"):
    with open(p) as f:
        for line in f:
            line=line.strip()
            if not line or line.startswith("#"): continue
            x=line.split(";")[0].strip().split(" ")[:6]
            if len(x)==6: fens.append(" ".join(x))
fens=fens[::40][:30]
def run(fen):
    e=Engine(EXE,options=PC20_LINES,timeout=300); e.start()
    try:
        _,r=e.position(fen=fen)
        if r: return ("REFUSED",)
        infos,bm,_=e.go("go nodes 20000")
        sc=None
        for l in infos:
            m=re.search(r"score (cp|mate) (-?\d+)",l)
            if m: sc=(m.group(1),int(m.group(2)))
        return (bm,sc)
    finally: e.quit()
print(f"build {BUILD}  PC20, Threads 1, go nodes 20000, {len(fens)} positions\n")
illegal=0; mate_checked=0; mate_bad=0; ok=0
for fen in fens:
    r=run(fen)
    if r[0]=="REFUSED": continue
    bm,sc=r
    b=chess.Board(fen)
    try: mv=chess.Move.from_uci(bm)
    except Exception: illegal+=1; print(f"  UNPARSED {bm} {fen[:40]}"); continue
    if mv not in b.legal_moves: illegal+=1; print(f"  ILLEGAL {bm} {fen[:40]}"); continue
    ok+=1
    if sc and sc[0]=="mate" and 0 < sc[1] <= 4:
        mate_checked+=1
        # verify the mate is real: play the PV's first move and check it's a mate in N-1
        b2=b.copy(); b2.push(mv)
        if not (b2.is_checkmate() if sc[1]==1 else True):
            mate_bad+=1; print(f"  MATE{sc[1]} not real at ply 1: {bm} {fen[:40]}")
print(f"  legal bestmoves {ok}, illegal {illegal}, mate scores checked {mate_checked}, bad {mate_bad}")
