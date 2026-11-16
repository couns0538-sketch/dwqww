#!/usr/bin/env python3
"""paired_depth.py — the DECISIVE question for match fairness, which is subtler than S-F49:
in a match, BOTH engines are given the same opening and the same node budget. If they reach the
same depth on that opening, the pair is balanced and any across-opening unevenness cancels.
Base (no options) vs PC r15 (PC20), ten openings, budgets 50000 and 250000."""
import os,re,sys
sys.path.insert(0,'/agent/repos/dwqww/forge-combo29/swarm/11')
from ucio import Engine
from pc20 import PC20_LINES
BASE_EXE="/home/ubuntu/builds/rel/forge"; PC_EXE="/tmp/pcbuild/forge"
SEQS=[
 ("Italian quiet",      "e2e4 e7e5 g1f3 b8c6 f1c4 f8c5 d2d3 g8f6 b1c3 d7d6"),
 ("Sicilian Najdorf",   "e2e4 c7c5 g1f3 d7d6 d2d4 c5d4 f3d4 g8f6 b1c3 a7a6"),
 ("French Winawer",     "e2e4 e7e6 d2d4 d7d5 b1c3 f8b4 e4e5 c7c5 a2a3 b4c3"),
 ("Caro-Kann Classical","e2e4 c7c6 d2d4 d7d5 b1c3 d5e4 c3e4 c8f5 e4g3 f5g6"),
 ("Queen's Gambit",     "d2d4 d7d5 c2c4 e7e6 b1c3 g8f6 c1g5 f8e7 e2e3 e8g8"),
 ("King's Indian",      "d2d4 g8f6 c2c4 g7g6 b1c3 f8g7 e2e4 d7d6 g1f3 e8g8"),
 ("English Opening",    "c2c4 e7e5 b1c3 g8f6 g2g3 d7d5 c4d5 f6d5 f1g2 d5b6"),
 ("Ruy Lopez closed",   "e2e4 e7e5 g1f3 b8c6 f1b5 a7a6 b5a4 g8f6 e1g1 f8e7"),
 ("Scandinavian",       "e2e4 d7d5 e4d5 d8d5 b1c3 d5a5 d2d4 g8f6 g1f3 c8f5"),
 ("London System",      "d2d4 g8f6 g1f3 d7d5 c1f4 c7c5 e2e3 b8c6 c2c3 d8b6"),
]
def run(exe,moves,N,opts):
    e=Engine(exe,options=opts,timeout=300); e.start()
    try:
        e.send("position startpos moves "+moves); e.send("isready"); e.read_until("readyok")
        infos,bm,_=e.go(f"go nodes {N}")
        d=None
        for l in infos:
            m=re.search(r"depth (\d+)",l)
            if m: d=int(m.group(1))
        return d,bm
    finally: e.quit()
print("paired depth: base (no options) vs PC r15 (PC20), Threads 1\n")
for N in (50000,250000):
    print(f"=== go nodes {N} ===")
    print(f"  {'opening':22} {'base d':>7} {'PC d':>5}  same-depth?")
    same=0; tot=0
    for label,mv in SEQS:
        b=run(BASE_EXE,mv,N,["Threads 1","Hash 16"])
        p=run(PC_EXE,mv,N,PC20_LINES)
        if b[0] is None or p[0] is None: continue
        tot+=1; eq=(b[0]==p[0]); same+=eq
        print(f"  {label:22} {b[0]:>7} {p[0]:>5}  {'yes' if eq else 'NO'}")
    print(f"  -> same depth on {same} of {tot} openings\n")
