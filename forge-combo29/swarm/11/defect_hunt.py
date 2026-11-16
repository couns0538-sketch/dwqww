#!/usr/bin/env python3
"""defect_hunt.py EXE BUILD — find counters where file 6's inequality DOES hold, i.e. where a
mate fits inside the remaining budget, and check the engine still finds it. A cp 0 THERE is a
real defect. For a mate in N the inequality is 2N-1 <= 100-H, so H <= 100-(2N-1).
mate in 1 -> H <= 99 ; mate in 3 -> H <= 97 ; mate in 5 -> H <= 95."""
import os,re,sys
sys.path.insert(0,'/agent/repos/dwqww/forge-combo29/swarm/11')
from ucio import Engine
from pc20 import PC20_LINES
EXE=sys.argv[1]; BUILD=sys.argv[2] if len(sys.argv)>2 else "?"
BOARDS=[("mate in 1 (white)","6k1/5ppp/8/8/8/8/5PPP/3Q2K1 w - - {h} 1"),
        ("mate in 1 (black)","3q2k1/5ppp/8/8/8/8/5PPP/6K1 b - - {h} 1")]
def probe(fen,depth=20):
    e=Engine(EXE,options=PC20_LINES,timeout=600); e.start()
    try:
        _,r=e.position(fen=fen)
        if r: return ("REFUSED",r[0])
        infos,bm,_=e.go(f"go depth {depth}")
        s=None
        for l in infos:
            m=re.search(r"score (cp|mate) (-?\d+)",l)
            if m: s=(m.group(1),int(m.group(2)))
        return (s,bm)
    finally: e.quit()
print(f"build {BUILD}  PC20, Threads 1, go depth 20")
print("mates in 1 must be FOUND for every H <= 99 (2*1-1=1 <= 100-H)\n")
print(f"{'board':20} {'H':>4} {'score':>12} {'bestmove':>9} {'must find?':>11} {'verdict'}")
bad=[]
for label,tpl in BOARDS:
    for H in (0,50,90,95,97,98,99,100):
        s,bm=probe(tpl.format(h=H))
        if s=="REFUSED": print(f"{label:20} {H:>4} REFUSED"); continue
        score = s           # s is already the (cp|mate, N) tuple; bm is separate
        must = (100-H) >= 1          # a mate in 1 needs 1 half-move
        found = score==("mate",1)
        v = "OK" if (found or not must) else "*** DEFECT: cp 0 where a mate fits ***"
        if must and not found: bad.append((label,H,score,bm))
        print(f"{label:20} {H:>4} {str(score):>12} {str(bm):>9} {str(must):>11} {v}")
print(f"\nreal defects found: {len(bad)}  {bad if bad else ''}")
