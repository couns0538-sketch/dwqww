#!/usr/bin/env python3
"""selfplay_long.py EXE BUILD N — longer soak: does a self-play game TERMINATE, or shuffle forever?
A game that never ends at softnodes 2000 would matter (the match program would need an adjudication)."""
import os,re,sys,time
sys.path.insert(0,'/agent/repos/dwqww/forge-combo29/swarm/11')
import chess
from ucio import Engine
from pc20 import PC20_LINES
EXE=sys.argv[1]; BUILD=sys.argv[2] if len(sys.argv)>2 else "?"
GAMES=int(sys.argv[3]) if len(sys.argv)>3 else 2
MAXPLY=400
print(f"build {BUILD}  PC20, Threads 1, softnodes 2000, up to {MAXPLY} plies/game\n")
for g in range(1,GAMES+1):
    b=chess.Board(); n=0; out="incomplete"; reps=0
    e=Engine(EXE,options=PC20_LINES,timeout=300); e.start()
    try:
        for ply in range(MAXPLY):
            if b.is_game_over(claim_draw=False):
                out = "mate" if b.is_checkmate() else ("stalemate" if b.is_stalemate() else
                      ("75-move" if b.halfmove_clock>=150 else "insufficient"))
                break
            if b.is_repetition(3): reps+=1
            _,r=e.position(fen=b.fen())
            if r: out="FEN-REFUSED"; break
            infos,bm,_=e.go("go softnodes 2000")
            if not bm or bm=="0000": out=f"0000"; break
            mv=chess.Move.from_uci(bm)
            if mv not in b.legal_moves: out=f"ILLEGAL {bm}"; break
            b.push(mv); n+=1
    finally: e.quit()
    print(f"  game {g}: {n} plies, halfmove clock {b.halfmove_clock}, outcome {out}, 3-fold positions passed {reps}")
