#!/usr/bin/env python3
"""multipv_real.py EXE BUILD — MultiPV 1..5 on PC20, Threads 1.
Checks: line count, distinct first moves, scores non-increasing, bestmove == multipv 1 move."""
import os,re,sys
sys.path.insert(0,'/agent/repos/dwqww/forge-combo29/swarm/11')
import chess
from ucio import Engine
from pc20 import PC20_LINES
EXE=sys.argv[1]; BUILD=sys.argv[2] if len(sys.argv)>2 else "?"
FEN="r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq - 3 3"
def run(mpv):
    opts=[l for l in PC20_LINES]
    e=Engine(EXE,options=opts+[f"setoption name MultiPV value {mpv}"],timeout=300); e.start()
    try:
        _,r=e.position(fen=FEN)
        if r: return None
        infos,bm,_=e.go("go nodes 20000")
        lines={}
        for l in infos:
            mm=re.search(r"multipv (\d+)",l)
            md=re.search(r"depth (\d+)",l)
            ms=re.search(r"score (cp|mate) (-?\d+)",l)
            mp=re.search(r" pv (\S+)",l)
            if mm and ms and mp:
                lines[int(mm.group(1))]=(ms.groups(),mp.group(1))
        return bm,lines
    finally: e.quit()
print(f"build {BUILD}  PC20, Threads 1, MultiPV 1..5, go nodes 20000\n")
b=chess.Board(FEN)
for mpv in (1,3,5):
    r=run(mpv)
    if r is None: print(f"  MultiPV {mpv}: REFUSED"); continue
    bm,lines=r
    ks=sorted(lines)
    moves=[lines[k][1] for k in ks]
    scores=[lines[k][0] for k in ks]
    distinct = len(set(moves))
    bm_is_first = (bm == lines[ks[0]][1]) if ks else None
    legal = all(chess.Move.from_uci(m) in b.legal_moves for m in moves)
    print(f"  MultiPV {mpv}: lines {len(ks)}, distinct first-moves {distinct}, bestmove==multipv1 {bm_is_first}, all legal {legal}")
    print(f"     scores {scores}")
