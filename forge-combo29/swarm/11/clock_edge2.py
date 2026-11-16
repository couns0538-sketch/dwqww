#!/usr/bin/env python3
"""clock_edge2.py EXE BUILD — the clock cases the first run never reached (movestogo, huge/zero
clocks, tiny movetime). Watches node counts so a slow answer is never read as a hang (trap 2b)."""
import os,re,sys,time
sys.path.insert(0,'/agent/repos/dwqww/forge-combo29/swarm/11')
import chess
from ucio import Engine
from pc20 import PC20_LINES
EXE=sys.argv[1]; BUILD=sys.argv[2] if len(sys.argv)>2 else "?"
FEN="r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq - 3 3"
b=chess.Board(FEN)
GO=["go wtime 6000 btime 6000 movestogo 1",
    "go wtime 6000 btime 6000 movestogo 40",
    "go wtime 6000 btime 6000 winc 0 binc 0",
    "go wtime 999999999 btime 999999999",
    "go wtime 0 btime 0",
    "go movetime 0",
    "go movetime 5"]
print(f"build {BUILD}  PC20, Threads 1\n")
for go in GO:
    e=Engine(EXE,options=PC20_LINES,timeout=200); e.start()
    try:
        _,r=e.position(fen=FEN)
        t0=time.monotonic()
        try:
            infos,bm,_=e.go(go,timeout=45)
            el=(time.monotonic()-t0)*1000
            nodes=0
            for l in infos:
                m=re.search(r"nodes (\d+)",l)
                if m: nodes=int(m.group(1))
            legal = bm=="0000" or (bm and chess.Move.from_uci(bm) in b.legal_moves)
            print(f"  {go:44} -> bm={str(bm):6} {el:8.0f} ms nodes={nodes:>9} legal={legal}")
        except Exception as ex:
            print(f"  {go:44} -> no bestmove within 45 s ({type(ex).__name__}) — check node advance")
    finally: e.quit()
