#!/usr/bin/env python3
"""inequality_test.py EXE BUILD — file 6's rule for whether a high-counter cp 0 is a DEFECT.
Rule: for a board at counter H that scores cp 0, the SAME board at counter 0 with go depth 20+
gives `mate N`. It is a DEFECT only if 2N-1 <= 100-H AND the real-counter board still scores
cp 0 at that same depth. Otherwise NOT a defect (the match program ends the game first)."""
import os,re,sys
sys.path.insert(0,'/agent/repos/dwqww/forge-combo29/swarm/11')
from ucio import Engine
from pc20 import PC20_LINES
EXE=sys.argv[1]; BUILD=sys.argv[2] if len(sys.argv)>2 else "?"
BOARDS=[
 ("white mate-in-1", "6k1/5ppp/8/8/8/8/5PPP/3Q2K1 w - - {h} 1", 100),
 ("black mate-in-1", "3q2k1/5ppp/8/8/8/8/5PPP/6K1 b - - {h} 1", 100),
 ("KRvK (seat05 case)", "1K6/8/8/3R4/8/8/8/k7 w - - {h} 1", 91),
 ("KQvK", "8/5K2/7Q/4k3/8/8/8/8 w - - {h} 1", 91),
]
def probe(fen,depth):
    e=Engine(EXE,options=PC20_LINES,timeout=600); e.start()
    try:
        _,r=e.position(fen=fen)
        if r: return ("REFUSED",r[0])
        infos,bm,_=e.go(f"go depth {depth}")
        score=None
        for l in infos:
            m=re.search(r"score (cp|mate) (-?\d+)",l)
            if m: score=(m.group(1),int(m.group(2)))
        return (score,bm)
    finally: e.quit()
print(f"build {BUILD}  settings PC20, Threads 1  (file 6 inequality test)\n")
print(f"{'board':22} {'H':>4} {'@counter0 d20':>16} {'mate N':>7} {'2N-1':>6} {'100-H':>6} {'defect?':>9}")
for label,tpl,H in BOARDS:
    zero=probe(tpl.format(h=0),20)
    real=probe(tpl.format(h=H),20)
    if zero[0]=="REFUSED" or real[0]=="REFUSED":
        print(f"{label:22} {H:>4}  MEASUREMENT FAILED {zero} {real}"); continue
    s0,bm0=zero; sH,bmH=real
    N=None
    if s0 and s0[0]=="mate" and s0[1]>0: N=s0[1]
    plies = (2*N-1) if N else None
    budget = 100-H
    is_defect = (N is not None and plies <= budget and sH==("cp",0))
    print(f"{label:22} {H:>4} {str(s0):>16} {str(N):>7} {str(plies):>6} {budget:>6} {str(is_defect):>9}   real-counter score={sH}")
