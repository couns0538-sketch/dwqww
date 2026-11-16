#!/usr/bin/env python3
"""clock_edge.py EXE BUILD — clock edge cases a GUI can send: only one side's time, missing
increment, movestogo, and absurd values. Check no hang, answer legal. PC20, Threads 1."""
import os,re,sys,time
sys.path.insert(0,'/agent/repos/dwqww/forge-combo29/swarm/11')
import chess
from ucio import Engine
from pc20 import PC20_LINES
EXE=sys.argv[1]; BUILD=sys.argv[2] if len(sys.argv)>2 else "?"
FEN="r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq - 3 3"
GO=["go wtime 6000","go btime 6000","go wtime 6000 btime 6000",
    "go wtime 6000 btime 6000 movestogo 1","go wtime 6000 btime 6000 movestogo 40",
    "go wtime 6000 btime 6000 winc 0 binc 0",
    "go wtime 999999999 btime 999999999","go wtime 0 btime 0",
    "go movetime 0","go movetime 1"]
b=chess.Board(FEN)
print(f"build {BUILD}  PC20, Threads 1\n")
for go in GO:
    e=Engine(EXE,options=PC20_LINES,timeout=120); e.start()
    try:
        _,r=e.position(fen=FEN)
        t0=time.monotonic()
        try:
            infos,bm,_=e.go(go,timeout=30)
            el=(time.monotonic()-t0)*1000
            legal = bm=="0000" or (bm and chess.Move.from_uci(bm) in b.legal_moves)
            print(f"  {go:46} -> bm={str(bm):6} {el:7.0f} ms legal={legal}")
        except Exception as ex:
            print(f"  {go:46} -> TIMEOUT/ERR {type(ex).__name__}")
    finally: e.quit()
