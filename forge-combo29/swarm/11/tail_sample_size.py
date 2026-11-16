#!/usr/bin/env python3
"""tail_sample_size.py EXE BUILD — how many runs does a TAIL claim need?
S-F94b showed 5 runs bound a median loosely. This measures how the observed p99/max of the
6s+0.06 clock grows with sample size, using 60 runs (the lesson applied to its own subject)."""
import sys,re,time,statistics
sys.path.insert(0,'/agent/repos/dwqww/forge-combo29/swarm/11')
from ucio import Engine
from pc20 import PC20_LINES
EXE=sys.argv[1]; BUILD=sys.argv[2] if len(sys.argv)>2 else "?"
N=int(sys.argv[3]) if len(sys.argv)>3 else 60
FEN="r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq - 3 3"
GO="go wtime 6000 btime 6000 winc 60 binc 60"
def one():
    e=Engine(EXE,options=PC20_LINES,timeout=180); e.start()
    try:
        _,r=e.position(fen=FEN)
        if r: return None
        t0=time.monotonic(); e.send(GO)
        e.read_until("bestmove",timeout=60)
        return (time.monotonic()-t0)*1000
    finally: e.quit()
print(f"build {BUILD}  PC20, Threads 1, {GO}, {N} runs\n")
ts=[t for t in (one() for _ in range(N)) if t]
ts.sort()
print(f"  n={len(ts)}  min {ts[0]:.1f}  median {statistics.median(ts):.1f}  max {ts[-1]:.1f} ms")
print(f"\n{'n':>4} {'median':>8} {'p99':>8} {'max':>8}")
for k in (5,10,20,30,60):
    if k>len(ts): continue
    sub=ts[:k]
    p99=sub[min(len(sub)-1,int(len(sub)*0.99))]
    print(f"{k:>4} {statistics.median(sub):8.1f} {p99:8.1f} {sub[-1]:8.1f}")
print("\n  If p99/max keep climbing with n, a 5-run sample cannot bound the tail at all.")
