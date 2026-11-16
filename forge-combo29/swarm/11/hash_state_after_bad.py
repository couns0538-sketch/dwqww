#!/usr/bin/env python3
"""hash_state_after_bad.py EXE BUILD — does a refused FEN leave the transposition table in a state
that changes a LATER, CORRECT search? Compare a clean search vs one preceded by a refused FEN.
This tests whether the damage is 'board only' or also 'hash'."""
import os,re,sys
sys.path.insert(0,'/agent/repos/dwqww/forge-combo29/swarm/11')
from ucio import Engine
from pc20 import PC20_LINES
EXE=sys.argv[1]; BUILD=sys.argv[2] if len(sys.argv)>2 else "?"
G1="r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq - 3 3"
BAD="4k3/8/8/8/8/8/8/4K3 w - -"
TARGET="rnbqkbnr/ppp2ppp/8/3pp3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 0 3"
def search(prefix_bad):
    e=Engine(EXE,options=PC20_LINES,timeout=300); e.start()
    try:
        e.position(fen=G1)
        if prefix_bad:
            e.send("position fen "+BAD); e.send("isready"); e.read_until("readyok")
        _,r=e.position(fen=TARGET)
        if r: return ("TARGET REFUSED",)
        infos,bm,_=e.go("go depth 12")
        n=None; sc=None
        for l in infos:
            m=re.search(r"nodes (\d+)",l)
            if m: n=int(m.group(1))
            ms=re.search(r"score (cp|mate) (-?\d+)",l)
            if ms: sc=ms.groups()
        return (bm,n,sc)
    finally: e.quit()
print(f"build {BUILD}  PC20, Threads 1, go depth 12 on {TARGET}\n")
clean=search(False); bad=search(True)
print(f"  clean search            : {clean}")
print(f"  after a refused FEN     : {bad}")
print(f"  identical: {clean==bad}")
print("  (identical => the refused command damages only the BOARD, not the transposition table;")
print("   different => the stale search also contaminated the hash, a wider blast radius.)")
