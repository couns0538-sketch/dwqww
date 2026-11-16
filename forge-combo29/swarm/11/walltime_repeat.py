#!/usr/bin/env python3
"""walltime_repeat.py EXE BUILD — applying trap 8's control to MY OWN timing claims.
S-F47 and S-F70 quoted wall-time medians; are those stable when the SAME binary is repeated?
This is the check I had not been running. Reports per-position spread over 5 repeats."""
import sys,re,time,statistics
sys.path.insert(0,'/agent/repos/dwqww/forge-combo29/swarm/11')
from ucio import Engine
from pc20 import PC20_LINES
EXE=sys.argv[1]; BUILD=sys.argv[2] if len(sys.argv)>2 else "?"
FEN="r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq - 3 3"
def one(go):
    e=Engine(EXE,options=PC20_LINES,timeout=180); e.start()
    try:
        _,r=e.position(fen=FEN)
        if r: return None
        t0=time.monotonic(); e.send(go)
        lines=e.read_until("bestmove",timeout=60)
        el=(time.monotonic()-t0)*1000
        bm=lines[-1].split()[1] if lines and lines[-1].startswith("bestmove") else None
        return (bm,el)
    finally: e.quit()
print(f"build {BUILD}  PC20, Threads 1 — SAME BINARY repeated 5x (trap 8's control)\n")
for go in ("go wtime 6000 btime 6000 winc 60 binc 60","go movetime 50","go nodes 20000"):
    rs=[one(go) for _ in range(5)]
    rs=[x for x in rs if x]
    if not rs: print(f"  {go:44} no results"); continue
    ts=[x[1] for x in rs]; ms=[x[0] for x in rs]
    spread=max(ts)-min(ts)
    print(f"  {go:44} wall ms {['%.1f'%t for t in ts]} spread {spread:5.1f} ms  move stable {len(set(ms))==1}")
print("\nIf the wall-time spread is a few ms, my S-F47/S-F70 medians stand as medians.")
print("If it is tens of ms, those figures were single-pass artefacts too.")
