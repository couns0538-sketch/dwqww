#!/usr/bin/env python3
"""deep_robust.py EXE BUILD — does the engine survive very deep searches without overflow or crash?
Tests go depth values up to the advertised max, plus absurd ones, on PC20 Threads 1."""
import os,re,sys,time
sys.path.insert(0,'/agent/repos/dwqww/forge-combo29/swarm/11')
import chess
from ucio import Engine
from pc20 import PC20_LINES
EXE=sys.argv[1]; BUILD=sys.argv[2] if len(sys.argv)>2 else "?"
FEN="8/6k1/3p4/3P2PP/4KP2/4N3/8/8 w - - 0 1"   # few pieces: deep reachable
def probe(go,timeout=120):
    e=Engine(EXE,options=PC20_LINES,timeout=timeout); e.start()
    try:
        _,r=e.position(fen=FEN)
        if r: return ("REFUSED",)
        t0=time.monotonic()
        infos,bm,_=e.go(go,timeout=timeout)
        el=time.monotonic()-t0
        d=None; n=None; sc=None
        for l in infos:
            md=re.search(r"depth (\d+)",l)
            if md: d=int(md.group(1))
            mn=re.search(r"nodes (\d+)",l)
            if mn: n=int(mn.group(1))
            ms=re.search(r"score (cp|mate) (-?\d+)",l)
            if ms: sc=ms.groups()
        return (bm,d,n,sc,round(el,1))
    finally: e.quit()
print(f"build {BUILD}  PC20, Threads 1  board {FEN}\n")
for go in ("go depth 20","go depth 40","go depth 64","go depth 100","go depth 100000"):
    try:
        r=probe(go,timeout=90)
        print(f"  {go:18} -> {r}")
    except Exception as ex:
        print(f"  {go:18} -> EXCEPTION {type(ex).__name__}: {str(ex)[:60]}")
