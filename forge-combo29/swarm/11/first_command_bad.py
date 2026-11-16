#!/usr/bin/env python3
"""first_command_bad.py EXE BUILD — a fresh process whose FIRST position command is malformed.
No previous board exists, so what does the engine search?"""
import os,re,sys
sys.path.insert(0,'/agent/repos/dwqww/forge-combo29/swarm/11')
import chess
from ucio import Engine
from pc20 import PC20_LINES
EXE=sys.argv[1]; BUILD=sys.argv[2] if len(sys.argv)>2 else "?"
CASES=[("truncated FEN first","position fen 4k3/8/8/8/8/8/8/4K3 w - -"),
       ("empty fen first","position fen"),
       ("illegal move first","position startpos moves e2e5"),
       ("two kings first","position fen 4k3/8/8/8/8/8/8/3KK3 w - - 0 1")]
print(f"build {BUILD}  PC20, Threads 1 — FRESH process, malformed FIRST command\n")
print(f"{'case':24} {'refusal':>52} {'perft1':>7} {'bm':>7} {'board':>10}")
for label,cmd in CASES:
    e=Engine(EXE,options=PC20_LINES,timeout=300); e.start()
    try:
        e.send(cmd); e.send("isready"); sync=e.read_until("readyok")
        ref=[l for l in sync if "invalid" in l or "illegal" in l]
        e.send("go perft 1"); lines=e.read_until("nodes ")
        n=None
        for l in lines:
            m=re.match(r"nodes (\d+)",l)
            if m: n=int(m.group(1))
        infos,bm,_=e.go("go softnodes 2000")
    finally: e.quit()
    which = "startpos(20)" if n==20 else ("KvK(5)" if n in (5,8) else f"{n}")
    print(f"{label:24} {str(ref)[:50]:>52} {str(n):>7} {str(bm):>7} {which:>10}")
