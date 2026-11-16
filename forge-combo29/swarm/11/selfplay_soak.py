#!/usr/bin/env python3
"""selfplay_soak.py EXE BUILD — play N complete games at the PC's self-play setting (softnodes 2000,
PC20, Threads 1) and check every move is legal, no hang, no crash. The most realistic soak."""
import os,re,sys,time
sys.path.insert(0,'/agent/repos/dwqww/forge-combo29/swarm/11')
import chess
from ucio import Engine
from pc20 import PC20_LINES
EXE=sys.argv[1]; BUILD=sys.argv[2] if len(sys.argv)>2 else "?"
GAMES=int(sys.argv[3]) if len(sys.argv)>3 else 3
MAXPLY=160
print(f"build {BUILD}  PC20, Threads 1, go softnodes 2000, {GAMES} games, max {MAXPLY} plies\n")
tot_moves=illegal=0; results=[]
t_all=time.monotonic()
for g in range(1,GAMES+1):
    b=chess.Board(); moves=[]; outcome="incomplete"
    # one process per game (the correct protocol, per HAZARD_stale_board.md)
    e=Engine(EXE,options=PC20_LINES,timeout=300); e.start()
    try:
        for ply in range(MAXPLY):
            if b.is_game_over(claim_draw=False):
                outcome = "mate" if b.is_checkmate() else ("stalemate" if b.is_stalemate() else "draw-rule")
                break
            _,r=e.position(fen=b.fen())
            if r: outcome="FEN-REFUSED"; break
            infos,bm,_=e.go("go softnodes 2000")
            if bm is None: outcome="NO-BESTMOVE(hang)"; break
            if bm=="0000":
                outcome="0000-with-legal-moves" if b.legal_moves.count()>0 else "terminal-0000"; break
            mv=chess.Move.from_uci(bm)
            if mv not in b.legal_moves:
                illegal+=1; outcome=f"ILLEGAL {bm}"; break
            b.push(mv); moves.append(bm); tot_moves+=1
    finally:
        e.quit()
    results.append((g,len(moves),outcome))
    print(f"  game {g}: {len(moves):3} plies, outcome {outcome}")
print(f"\n  total moves {tot_moves}, illegal {illegal}, wall {time.monotonic()-t_all:.0f}s")
