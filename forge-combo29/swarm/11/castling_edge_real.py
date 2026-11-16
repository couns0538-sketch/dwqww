#!/usr/bin/env python3
"""castling_edge_real.py EXE BUILD — castling edge cases that a real GUI could send, on PC20.
Checks the castling MOVE is generated exactly when legal, via divide."""
import os,re,sys
sys.path.insert(0,'/agent/repos/dwqww/forge-combo29/swarm/11')
import chess
from ucio import Engine
from pc20 import PC20_LINES
EXE=sys.argv[1]; BUILD=sys.argv[2] if len(sys.argv)>2 else "?"
CASES=[
 ("both sides can castle",  "r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1"),
 ("king in check: no castle","r3k2r/8/8/8/8/8/4r3/R3K2R w KQkq - 0 1"),
 ("f1 attacked: no O-O",    "r3k2r/8/8/8/8/8/5r2/R3K2R w KQkq - 0 1"),
 ("b1 attacked: O-O-O ok",  "r3k2r/8/8/8/8/8/1r6/R3K2R w KQkq - 0 1"),
 ("rights gone",            "r3k2r/8/8/8/8/8/8/R3K2R w - - 0 1"),
]
def divide(fen):
    e=Engine(EXE,options=PC20_LINES,timeout=300); e.start()
    try:
        _,r=e.position(fen=fen)
        if r: return None,None
        e.send("go perft 1"); lines=e.read_until("nodes ",timeout=60)
        mv=[]; tot=None
        for l in lines:
            m=re.match(r"([a-h][1-8][a-h][1-8][qrbn]?): (\d+)",l)
            if m: mv.append(m.group(1))
            m2=re.match(r"nodes (\d+)",l)
            if m2: tot=int(m2.group(1))
        return mv,tot
    finally: e.quit()
print(f"build {BUILD}  PC20, Threads 1\n")
print(f"{'case':26} {'engine':>6} {'py':>4} {'match':>6} {'O-O?':>5} {'O-O-O?':>7} {'agree':>6}")
for label,fen in CASES:
    b=chess.Board(fen)
    mv,tot=divide(fen)
    if mv is None: print(f"  {label:26} REFUSED"); continue
    py=sorted(m.uci() for m in b.legal_moves)
    eO = "e1g1" in mv; eOO="e1c1" in mv
    pO = "e1g1" in py; pOO="e1c1" in py
    print(f"{label:26} {tot:>6} {len(py):>4} {str(tot==len(py)):>6} {str(eO):>5} {str(eOO):>7} {str(eO==pO and eOO==pOO):>6}")
