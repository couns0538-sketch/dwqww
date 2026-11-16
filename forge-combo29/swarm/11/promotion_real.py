#!/usr/bin/env python3
"""promotion_real.py EXE BUILD — promotions generated with all four pieces, capture-promotions too.
Divide-verified against python-chess on PC20, Threads 1."""
import os,re,sys
sys.path.insert(0,'/agent/repos/dwqww/forge-combo29/swarm/11')
import chess
from ucio import Engine
from pc20 import PC20_LINES
EXE=sys.argv[1]; BUILD=sys.argv[2] if len(sys.argv)>2 else "?"
CASES=[
 ("push promo (a7-a8)",    "4k3/P7/8/8/8/8/8/4K3 w - - 0 1"),
 ("push+capture promo",    "1r2k3/P7/8/8/8/8/8/4K3 w - - 0 1"),
 ("black promo",           "4k3/8/8/8/8/8/7p/4K3 b - - 0 1"),
 ("promo with check",      "5k2/P7/8/8/8/8/8/4K3 w - - 0 1"),
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
for label,fen in CASES:
    b=chess.Board(fen)
    mv,tot=divide(fen)
    if mv is None: print(f"  {label}: REFUSED"); continue
    py=sorted(m.uci() for m in b.legal_moves)
    promos_e=sorted(m for m in mv if len(m)==5)
    promos_p=sorted(m for m in py if len(m)==5)
    print(f"  {label}")
    print(f"    engine {tot} = py {len(py)}: {tot==len(py)}")
    print(f"    engine promos {promos_e}")
    print(f"    py     promos {promos_p}   same={promos_e==promos_p}")
