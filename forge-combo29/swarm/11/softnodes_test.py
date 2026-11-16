#!/usr/bin/env python3
"""softnodes_test.py EXE BUILD — file 6's new area: `go softnodes N` on PC20, Threads 1.
Answers: (1) deterministic run to run? (2) does it stop at a FINISHED depth? (3) how far past N?"""
import os,re,sys
sys.path.insert(0,'/agent/repos/dwqww/forge-combo29/swarm/11')
from ucio import Engine
from pc20 import PC20_LINES
EXE=sys.argv[1]; BUILD=sys.argv[2] if len(sys.argv)>2 else "?"
FEN="r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq - 3 3"
def run(N):
    e=Engine(EXE,options=PC20_LINES,timeout=300); e.start()
    try:
        _,r=e.position(fen=FEN)
        if r: return ("REFUSED",r[0])
        infos,bm,_=e.go(f"go softnodes {N}")
        lines=[]
        for l in infos:
            d=re.search(r"depth (\d+)",l); n=re.search(r"nodes (\d+)",l)
            s=re.search(r"score (cp|mate) (-?\d+)",l)
            if d and n: lines.append((int(d.group(1)),int(n.group(1)), s.groups() if s else None))
        return (bm, lines)
    finally: e.quit()
print(f"build {BUILD}  PC20, Threads 1  FEN {FEN}\n")
for N in (2000, 20000):
    print(f"=== go softnodes {N} ===")
    outs=[run(N) for _ in range(3)]
    for i,(bm,lines) in enumerate(outs,1):
        if bm=="REFUSED": print(f"  run {i}: REFUSED"); continue
        last=lines[-1] if lines else None
        print(f"  run {i}: bestmove={bm} depth_reached={last[0] if last else '?'} "
              f"nodes={last[1] if last else '?'} score={last[2] if last else '?'}")
    det = all(o==outs[0] for o in outs)
    print(f"  DETERMINISTIC: {det}")
    if outs[0][0]!="REFUSED" and outs[0][1]:
        lastN=outs[0][1][-1][1]
        print(f"  stopped at depth {outs[0][1][-1][0]} with {lastN} nodes; went {lastN-N} past N "
              f"({(lastN-N)/N*100:.1f}% over)")
    print()
