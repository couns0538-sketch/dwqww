#!/usr/bin/env python3
"""ending_truth.py EXE BUILD — simple endings with KNOWN outcomes: does the engine's score and
move agree with truth? (KQvK, KRvK won; KvK, KNvK, KBvK drawn; KQvKR won.) PC20, Threads 1."""
import os,re,sys
sys.path.insert(0,'/agent/repos/dwqww/forge-combo29/swarm/11')
import chess
from ucio import Engine
from pc20 import PC20_LINES
EXE=sys.argv[1]; BUILD=sys.argv[2] if len(sys.argv)>2 else "?"
CASES=[
 ("KQ v K  (win)",  "6k1/8/8/8/8/8/8/4QK2 w - - 0 1", "win"),
 ("KR v K  (win)",  "6k1/8/8/8/8/8/8/4RK2 w - - 0 1", "win"),
 ("K v K   (draw)", "6k1/8/8/8/8/8/8/4K3 w - - 0 1", "draw"),
 ("KN v K  (draw)", "6k1/8/8/8/8/8/8/3NK3 w - - 0 1", "draw"),
 ("KB v K  (draw)", "6k1/8/8/8/8/8/8/3BK3 w - - 0 1", "draw"),
 ("KNN v K (draw, cannot force)", "6k1/8/8/8/8/8/8/2NNK3 w - - 0 1", "draw-ish"),
 ("KQ v KR (win)",  "4k1r1/8/8/8/8/8/8/3QK3 w - - 0 1", "win"),
]
def probe(fen,depth=16):
    e=Engine(EXE,options=PC20_LINES,timeout=600); e.start()
    try:
        _,r=e.position(fen=fen)
        if r: return None
        infos,bm,_=e.go(f"go depth {depth}",timeout=300)
        sc=None; n=None
        for l in infos:
            m=re.search(r"score (cp|mate) (-?\d+)",l)
            if m: sc=(m.group(1),int(m.group(2)))
            mn=re.search(r"nodes (\d+)",l)
            if mn: n=int(mn.group(1))
        return (bm,sc,n)
    finally: e.quit()
print(f"build {BUILD}  PC20, Threads 1, go depth 16\n{'case':32} {'expect':10} {'score':14} {'bm':7} {'agree?'}")
for label,fen,expect in CASES:
    r=probe(fen)
    if r is None: print(f"{label:32} REFUSED"); continue
    bm,sc,n=r
    if expect=="win":
        ok = sc and (sc[0]=="mate" or (sc[0]=="cp" and sc[1]>200))
    elif expect=="draw":
        ok = sc and sc[0]=="cp" and abs(sc[1])<=50
    else:
        ok = sc is not None
    print(f"{label:32} {expect:10} {str(sc):14} {bm:7} {ok}")
