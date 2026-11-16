#!/usr/bin/env python3
"""clock_6s.py EXE BUILD — the owner's strength-match clock: 6 s + 0.06 per move.
PC20, Threads 1. Measures wall time per move and checks for overruns of the 6 s budget."""
import os,re,sys,time,statistics
sys.path.insert(0,'/agent/repos/dwqww/forge-combo29/swarm/11')
from ucio import Engine
from pc20 import PC20_LINES
EXE=sys.argv[1]; BUILD=sys.argv[2] if len(sys.argv)>2 else "?"
fens=[]
with open("positions/G_set_G.epd") as f:
    for line in f:
        line=line.strip()
        if not line or line.startswith("#"): continue
        x=line.split(";")[0].strip().split(" ")[:6]
        if len(x)==6: fens.append(" ".join(x))
        if len(fens)>=20: break
def one(fen):
    e=Engine(EXE,options=PC20_LINES,timeout=120); e.start()
    try:
        _,r=e.position(fen=fen)
        if r: return None
        t0=time.monotonic()
        e.send("go wtime 6000 btime 6000 winc 60 binc 60")
        infos,bm,_=e.go("",timeout=60) if False else (None,None,None)
        # go() sends its own line; drive manually instead
        e.read_until("bestmove",timeout=60)
        return (time.monotonic()-t0)*1000
    finally: e.quit()
print(f"build {BUILD}  PC20, Threads 1, go wtime 6000 btime 6000 winc 60 binc 60, {len(fens)} G positions\n")
ts=[]
for fen in fens:
    try:
        t=one(fen)
        if t: ts.append(t)
    except Exception as ex:
        print("  FAIL",ex)
ts.sort()
print(f"  moves measured {len(ts)}")
print(f"  median {statistics.median(ts):.0f} ms, p99 {ts[int(len(ts)*0.99)-1]:.0f} ms, max {max(ts):.0f} ms")
print(f"  over the 6000 ms clock: {sum(1 for t in ts if t>6000)}")
