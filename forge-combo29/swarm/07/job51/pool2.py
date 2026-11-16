#!/usr/bin/env python3
"""Find positions where the engine reports a mate at the SMALLEST match budget (20k nodes).
Scan set G plus constructed mates-in-2..4 so the kept set is large enough to measure a rate."""
import sys, json
sys.path.insert(0,'.')
from mate_rich import run, PC20
import chess

cands=[]
# set G
for line in open('/tmp/set_G.epd',encoding='utf-8'):
    p=line.split()
    if len(p)>=4:
        f=" ".join(p[:6]) if len(p)>=6 else " ".join(p[:4])+" 0 1"
        try: chess.Board(f)
        except ValueError: continue
        cands.append(f)
# constructed mates-in-1..3: K+Q and K+R and K+2Q against a cornered king
extra=[
 "7k/6Q1/6K1/8/8/8/8/8 b - - 0 1","6k1/5Q2/6K1/8/8/8/8/8 b - - 0 1",
 "8/8/8/8/8/5k2/8/5K1Q w - - 0 1","8/8/8/8/8/5k2/8/5K1R w - - 0 1",
 "2k5/8/1K6/8/8/8/8/1Q6 w - - 0 1","8/2k5/8/1K6/8/8/8/7Q w - - 0 1",
 "8/8/8/3k4/8/3K4/8/7R w - - 0 1","8/8/8/8/1k6/8/1K6/7R w - - 0 1",
]
cands+=extra
exe=sys.argv[1]; out=sys.argv[2]
kept=[]
for i,f in enumerate(cands):
    r=run(exe,f,"go nodes 20000")
    if r["mate"] is not None:
        kept.append({"fen":f,"mate":r["mate"],"pv":r["pv"]})
    if (i+1)%40==0: print(f"  scanned {i+1}/{len(cands)}  kept {len(kept)}",flush=True)
print(f"kept {len(kept)} of {len(cands)} positions that report a mate at go nodes 20000")
json.dump(kept,open(out+"/pool2.json","w"),indent=1)
