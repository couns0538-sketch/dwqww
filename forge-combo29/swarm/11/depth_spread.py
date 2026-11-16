#!/usr/bin/env python3
"""depth_spread.py EXE BUILD — the question that decides if node-limited matches are FAIR:
at a fixed node budget, do DIFFERENT openings reach the SAME depth? If yes, a node-limited
match is fair in practice; if the spread is wide, it is unequal.

Ten distinct openings (moves from startpos), PC20, Threads 1, budgets 50000 and 250000.
Reports the depth each opening completes and the spread."""
import os,re,sys,statistics
sys.path.insert(0,'/agent/repos/dwqww/forge-combo29/swarm/11')
from ucio import Engine
from pc20 import PC20_LINES
EXE=sys.argv[1]; BUILD=sys.argv[2] if len(sys.argv)>2 else "?"
OPENINGS=[
 ("Sicilian Najdorf","e2e4 c7c5 g1f3 d6 4".replace(" 4",""),None),
]
# ten real opening move sequences (all legal, all distinct)
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
def run(moves,N):
    e=Engine(EXE,options=PC20_LINES,timeout=300); e.start()
    try:
        e.send("position startpos moves "+moves); e.send("isready")
        if [l for l in e.read_until("readyok") if "invalid" in l or "illegal" in l]:
            return None
        infos,bm,_=e.go(f"go nodes {N}")
        d=n=None
        for l in infos:
            md=re.search(r"depth (\d+)",l); mn=re.search(r"nodes (\d+)",l)
            if md: d=int(md.group(1))
            if mn: n=int(mn.group(1))
        return (d,n,bm)
    finally: e.quit()
print(f"build {BUILD}  PC20, Threads 1 — ten DIFFERENT openings at a fixed node budget\n")
for N in (50000,250000):
    print(f"=== go nodes {N} ===")
    ds=[]
    for label,mv in SEQS:
        r=run(mv,N)
        if r is None: print(f"  {label:22} FAILED"); continue
        d,n,bm=r
        ds.append(d)
        print(f"  {label:22} depth {d:2}  nodes {n:7}  bm {bm}")
    if ds:
        print(f"  -> depth spread: min {min(ds)}, max {max(ds)}, range {max(ds)-min(ds)}, "
              f"median {statistics.median(ds)}  ({'EQUAL' if max(ds)==min(ds) else 'UNEQUAL'})")
    print()
