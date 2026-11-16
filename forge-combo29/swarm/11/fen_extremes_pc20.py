#!/usr/bin/env python3
"""fen_extremes_pc20.py EXE BUILD — long-input and pathological FENs on the PC's build.
Checks the 3000-char control and a few structural extremes, with perft 1 where accepted."""
import os,re,sys
sys.path.insert(0,'/agent/repos/dwqww/forge-combo29/swarm/11')
import chess
from ucio import Engine
from pc20 import PC20_LINES
EXE=sys.argv[1]; BUILD=sys.argv[2] if len(sys.argv)>2 else "?"
CASES=[
 ("3000-char first field", "P"*3000+" w - - 0 1"),
 ("3000 chars of '8/'",    "8/"*1500+" w - - 0 1"),
 ("3000 spaces then valid"," "*3000+"4k3/8/8/8/8/8/8/4K3 w - - 0 1"),
 ("70 ranks",              "/".join(["8"]*70)+" w - - 0 1"),
 ("rank of 64 digits",     "4"+"4"*63+"/8/8/8/8/8/8/8 w - - 0 1"),
 ("10000-char move list",  "4k3/8/8/8/8/8/8/4K3 w - - 0 1"),
]
def probe(fen, moves=None):
    e=Engine(EXE,options=PC20_LINES,timeout=300); e.start()
    try:
        if moves is not None:
            e.send("position startpos moves "+moves)
        else:
            e.send("position fen "+fen)
        e.send("isready"); sync=e.read_until("readyok",timeout=60)
        ref=[l for l in sync if "invalid" in l or "illegal" in l]
        if ref: return ("REFUSED", ref[0][:80])
        e.send("go perft 1"); lines=e.read_until("nodes ",timeout=60)
        n=None
        for l in lines:
            m=re.match(r"nodes (\d+)",l)
            if m: n=int(m.group(1))
        return ("ACCEPTED", n)
    finally: e.quit()
print(f"build {BUILD}  PC20, Threads 1\n")
for label,fen in CASES[:-1]:
    try:
        st,v=probe(fen)
        print(f"  {label:26} -> {st:9} {v}")
    except Exception as ex:
        print(f"  {label:26} -> EXCEPTION {type(ex).__name__}: {str(ex)[:50]}")
# 10000-ply move list: repeat a legal shuffle cycle
cyc="g1f3 g8f6 f3g1 f6g8 "*1250
try:
    st,v=probe(None,cyc.strip())
    print(f"  {'10000-ply move list':26} -> {st:9} {v}")
except Exception as ex:
    print(f"  {'10000-ply move list':26} -> EXCEPTION {type(ex).__name__}: {str(ex)[:50]}")
