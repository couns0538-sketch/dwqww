#!/usr/bin/env python3
"""clock_game.py EXE BUILD — a full game on the owner's strength clock 6s+0.06, PC20, Threads 1.
Tracks both clocks honestly (deducting elapsed time, adding increment) and reports any flag fall."""
import os,re,sys,time
sys.path.insert(0,'/agent/repos/dwqww/forge-combo29/swarm/11')
import chess
from ucio import Engine
from pc20 import PC20_LINES
EXE=sys.argv[1]; BUILD=sys.argv[2] if len(sys.argv)>2 else "?"
MAXPLY=int(sys.argv[3]) if len(sys.argv)>3 else 120
print(f"build {BUILD}  PC20, Threads 1, wtime/btime 6000 ms + 60 ms increment, up to {MAXPLY} plies\n")
b=chess.Board(); w=6000.0; bl=6000.0; n=0; worst=0.0; out="incomplete"
e=Engine(EXE,options=PC20_LINES,timeout=300); e.start()
try:
    for ply in range(MAXPLY):
        if b.is_game_over(claim_draw=False):
            out = "mate" if b.is_checkmate() else ("stalemate" if b.is_stalemate() else "draw")
            break
        _,r=e.position(fen=b.fen())
        if r: out="FEN-REFUSED"; break
        t0=time.monotonic()
        e.send(f"go wtime {int(w)} btime {int(bl)} winc 60 binc 60")
        lines=e.read_until("bestmove",timeout=60)
        el=(time.monotonic()-t0)*1000
        bm=lines[-1].split()[1] if lines and lines[-1].startswith("bestmove") else None
        if not bm or bm=="0000": out=f"0000"; break
        mv=chess.Move.from_uci(bm)
        if mv not in b.legal_moves: out=f"ILLEGAL {bm}"; break
        white = b.turn==chess.WHITE
        if white: w = w - el + 60
        else:     bl = bl - el + 60
        worst=max(worst,el)
        if (white and w<0) or ((not white) and bl<0):
            out=f"FLAG FALL (used {el:.0f} ms)"; break
        b.push(mv); n+=1
finally: e.quit()
print(f"  plies {n}, outcome {out}")
print(f"  clocks left: white {w:.0f} ms, black {bl:.0f} ms; slowest single move {worst:.0f} ms")
print(f"  (a flag fall here would mean the clock path overruns the budget the GUI gave it)")
