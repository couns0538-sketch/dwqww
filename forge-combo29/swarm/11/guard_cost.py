#!/usr/bin/env python3
"""guard_cost.py EXE BUILD — what does the defence COST? Time for ucinewgame + resend vs nothing,
and whether the search result after a fixup is identical to a clean search (no performance penalty)."""
import os,re,sys,time
sys.path.insert(0,'/agent/repos/dwqww/forge-combo29/swarm/11')
import chess
from ucio import Engine
from pc20 import PC20_LINES
EXE=sys.argv[1]; BUILD=sys.argv[2] if len(sys.argv)>2 else "?"
GOOD="rnbqkbnr/ppp2ppp/8/3pp3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 0 3"
BAD="4k3/8/8/8/8/8/8/4K3 w - -"
def scenario(fixup):
    e=Engine(EXE,options=PC20_LINES,timeout=300); e.start()
    try:
        e.position(fen=GOOD)
        t0=time.monotonic()
        if fixup:
            e.send("position fen "+BAD); e.send("isready"); e.read_until("readyok")
            e.send("ucinewgame"); e.send("isready"); e.read_until("readyok")
            e.send("position fen "+GOOD); e.send("isready"); e.read_until("readyok")
        overhead=(time.monotonic()-t0)*1000
        infos,bm,_=e.go("go depth 12")
        n=None; sc=None
        for l in infos:
            m=re.search(r"nodes (\d+)",l)
            if m: n=int(m.group(1))
            ms=re.search(r"score (cp|mate) (-?\d+)",l)
            if ms: sc=ms.groups()
        return overhead,bm,n,sc
    finally: e.quit()
print(f"build {BUILD}  PC20, Threads 1\n")
oh1,bm1,n1,s1=scenario(False)
oh2,bm2,n2,s2=scenario(True)
print(f"  clean            : overhead {oh1:5.1f} ms  bm={bm1} nodes={n1} score={s1}")
print(f"  after fixup      : overhead {oh2:5.1f} ms  bm={bm2} nodes={n2} score={s2}")
print(f"  same search result: {bm1==bm2 and n1==n2 and s1==s2}")
print(f"  cost of the defence: {oh2-oh1:.1f} ms per recovery")
