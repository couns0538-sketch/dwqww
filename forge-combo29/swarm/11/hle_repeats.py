#!/usr/bin/env python3
"""hle_repeats.py — seat 07 says a node count at an 11-60 ms clock is not stable on either build,
so my S-F91 "ON stable 5/5" may have been luck. Test: repeat each differing value 8 times per build
and report MOVE stability and NODE stability SEPARATELY."""
import sys,re
sys.path.insert(0,'/agent/repos/dwqww/forge-combo29/swarm/11')
from ucio import Engine
from pc20 import PC20_LINES
ON="/tmp/pcbuild/forge"; OFF="/tmp/pchlebuild/forge"
FEN="r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq - 3 3"
def run(exe,t):
    e=Engine(exe,options=PC20_LINES,timeout=60); e.start()
    try:
        _,r=e.position(fen=FEN)
        if r: return None
        infos,bm,_=e.go(f"go wtime {t} btime {t}",timeout=10)
        n=0
        for l in infos:
            m=re.search(r"nodes (\d+)",l)
            if m: n=int(m.group(1))
        return (bm,n)
    finally: e.quit()
R=8
print(f"8 repeats per value, fresh process each. ON=shipped, OFF=switch flipped off\n")
print(f"{'t':>3} {'build':>5} {'moves seen':22} {'move stable':>11} {'nodes seen':26} {'node stable':>11}")
for t in (11,16,17,27,28,31):
    for name,exe in (("ON",ON),("OFF",OFF)):
        rs=[run(exe,t) for _ in range(R)]
        rs=[x for x in rs if x]
        if not rs: print(f"{t:>3} {name:>5} (no results)"); continue
        mv=sorted({x[0] for x in rs}); nn=sorted({x[1] for x in rs})
        print(f"{t:>3} {name:>5} {','.join(mv)[:22]:22} {str(len(mv)==1):>11} {','.join(str(x) for x in nn)[:26]:26} {str(len(nn)==1):>11}")
