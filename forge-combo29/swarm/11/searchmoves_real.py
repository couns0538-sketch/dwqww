#!/usr/bin/env python3
"""searchmoves_real.py EXE BUILD — does searchmoves actually RESTRICT the search to named legal moves
on the PC's path? (Different from the 0000 case: here the named moves ARE legal.)"""
import os,re,sys
sys.path.insert(0,'/agent/repos/dwqww/forge-combo29/swarm/11')
import chess
from ucio import Engine
from pc20 import PC20_LINES
EXE=sys.argv[1]; BUILD=sys.argv[2] if len(sys.argv)>2 else "?"
FEN="r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq - 3 3"
b=chess.Board(FEN)
def run(go):
    e=Engine(EXE,options=PC20_LINES,timeout=300); e.start()
    try:
        _,r=e.position(fen=FEN)
        if r: return None
        infos,bm,_=e.go(go)
        return bm
    finally: e.quit()
legal=sorted(m.uci() for m in b.legal_moves)
print(f"build {BUILD}  PC20, Threads 1\nFEN has {len(legal)} legal moves\n")
free=run("go nodes 20000")
print(f"  unrestricted go        -> {free}")
for sub in (legal[:1], legal[:3], [legal[0],legal[-1]]):
    bm=run("go nodes 20000 searchmoves "+" ".join(sub))
    inside = bm in sub
    print(f"  searchmoves {' '.join(sub):22} -> {bm}  {'INSIDE the set (correct)' if inside else '*** OUTSIDE the set ***'}")
