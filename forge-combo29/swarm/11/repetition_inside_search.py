#!/usr/bin/env python3
"""repetition_inside_search.py EXE BUILD — the question that decides whether the repetition door
matters: does the 0-node adjudication fire only at the ROOT, or also at nodes INSIDE a search?
If only at the root, the arbiter explanation holds fully (the game would already be over).
If inside the search too, it could distort evaluation of lines involving repetition."""
import sys,re
sys.path.insert(0,'/agent/repos/dwqww/forge-combo29/swarm/11')
import chess
from ucio import Engine
EXE=sys.argv[1]; BUILD=sys.argv[2] if len(sys.argv)>2 else "?"
base=chess.Board()
# Build a position where a repetition is reachable INSIDE the tree: startpos, then a knight shuffle
# is available. Search deep and see if the score collapses to 0 spuriously.
FENS=[
 ("startpos (knight shuffle available)","rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"),
 ("quiet equal middlegame","r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 3 3"),
]
def run(fen,depth):
    e=Engine(EXE,options=[],timeout=300); e.start()
    try:
        _,r=e.position(fen=fen)
        if r: return None
        infos,bm,_=e.go(f"go depth {depth}",timeout=200)
        n=0; sc=None; pv=[]
        for l in infos:
            m=re.search(r"nodes (\d+)",l)
            if m: n=int(m.group(1))
            ms=re.search(r"score (cp|mate) (-?\d+)",l)
            if ms: sc=ms.groups()
            mp=re.search(r" pv (.+)$",l)
            if mp: pv=mp.group(1).split()
        return (sc,n,bm,pv)
    finally: e.quit()
print(f"build {BUILD}  Threads 1 — does depth raise or collapse the score?\n")
for label,fen in FENS:
    for d in (8,12,16):
        r=run(fen,d)
        if r is None: print(f"  {label}: {d} REFUSED"); continue
        sc,n,bm,pv=r
        print(f"  {label:38} d{d:2} score={str(sc):14} nodes={n:>9} bm={bm}")
    print()
print("A 0-node / cp 0 collapse at the ROOT would show nodes=0. Non-zero nodes here means the")
print("repetition adjudication did not fire at these roots, which is the expected behaviour.")
