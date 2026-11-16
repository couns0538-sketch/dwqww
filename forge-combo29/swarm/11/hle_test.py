#!/usr/bin/env python3
"""hle_test.py — HARD_LIMIT_EMERGENCY: the source says it matters for a clock 1-2 ms above Move
Overhead (10 ms), e.g. `go wtime 11`. Compare shipped(ON) vs OFF there: does the move or the
search effort differ?"""
import sys
sys.path.insert(0,'/agent/repos/dwqww/forge-combo29/swarm/11')
import chess
from ucio import Engine
from pc20 import PC20_LINES
ON="/tmp/pcbuild/forge"; OFF="/tmp/pchlebuild/forge"
FEN="r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq - 3 3"
GO=["go wtime 11 btime 11","go wtime 12 btime 12","go wtime 15 btime 15","go wtime 30 btime 30"]
def run(exe,go):
    e=Engine(exe,options=PC20_LINES,timeout=120); e.start()
    try:
        _,r=e.position(fen=FEN)
        if r: return None
        infos,bm,_=e.go(go,timeout=30)
        n=0; d=0
        for l in infos:
            import re
            m=re.search(r"nodes (\d+)",l)
            if m: n=int(m.group(1))
            md=re.search(r"depth (\d+)",l)
            if md: d=int(md.group(1))
        return (bm,d,n)
    finally: e.quit()
print("HARD_LIMIT_EMERGENCY: shipped(ON) vs this-build(OFF)\n")
for go in GO:
    a=run(ON,go); b=run(OFF,go)
    ch = "CHANGED" if a!=b else "same"
    print(f"  {go:22} ON={str(a):26} OFF={str(b):26} {ch}")
