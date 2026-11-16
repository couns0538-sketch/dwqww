#!/usr/bin/env python3
"""fen_incheck_real.py EXE BUILD — FENs where the side to move is IN CHECK, on the real path.
The engine must find only evasions; check that perft 1 and the bestmove are legal."""
import os,re,sys
sys.path.insert(0,'/agent/repos/dwqww/forge-combo29/swarm/11')
import chess
from ucio import Engine
from pc20 import PC20_LINES
EXE=sys.argv[1]; BUILD=sys.argv[2] if len(sys.argv)>2 else "?"
CASES=[
 ("single check (rook)", "4k3/8/8/8/8/8/8/4K2r w - - 0 1"),
 ("double check",        "4k3/8/8/8/8/8/8/4K2r w - - 0 1"),
 ("check by knight",     "4k3/8/8/8/8/5n2/8/4K3 w - - 0 1"),
 ("check + mate in 1",   "6k1/5ppp/8/8/8/8/5PPP/3Q2K1 w - - 0 1"),
 ("pinned piece check",  "4k3/8/8/8/8/8/4r3/4K3 w - - 0 1"),
]
def probe(fen):
    e=Engine(EXE,options=PC20_LINES,timeout=300); e.start()
    try:
        _,r=e.position(fen=fen)
        if r: return ("REFUSED", r[0][:60])
        e.send("go perft 1"); lines=e.read_until("nodes ")
        n=None
        for l in lines:
            m=re.match(r"nodes (\d+)",l)
            if m: n=int(m.group(1))
        infos,bm,_=e.go("go softnodes 2000")
        return (n,bm)
    finally: e.quit()
print(f"build {BUILD}  PC20, Threads 1\n")
print(f"{'case':22} {'py-perft1':>9} {'engine':>7} {'evasions match':>15} {'bestmove':>9} {'legal':>6}")
for label,fen in CASES:
    b=chess.Board(fen)
    py=b.legal_moves.count()
    r=probe(fen)
    if r[0]=="REFUSED": print(f"{label:22} REFUSED {r[1]}"); continue
    n,bm=r
    legal = chess.Move.from_uci(bm) in b.legal_moves if bm and bm not in ("0000",) else (bm=="0000" and py==0)
    print(f"{label:22} {py:>9} {n:>7} {str(n==py):>15} {str(bm):>9} {str(legal):>6}")
