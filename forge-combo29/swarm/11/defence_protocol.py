#!/usr/bin/env python3
"""defence_protocol.py EXE BUILD — test candidate harness protocols against the stale-board hazard.
P1 no defence.  P2 ucinewgame before every position.  P3 fresh process per game.
Which protocols return the CORRECT game-3 move after a bad FEN?"""
import os,re,sys
sys.path.insert(0,'/agent/repos/dwqww/forge-combo29/swarm/11')
import chess
from ucio import Engine
from pc20 import PC20_LINES
EXE=sys.argv[1]; BUILD=sys.argv[2] if len(sys.argv)>2 else "?"
G1="r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq - 3 3"
BAD="4k3/8/8/8/8/8/8/4K3 w - -"
G3="rnbqkbnr/ppp2ppp/8/3pp3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 0 3"
b1=chess.Board(G1); b3=chess.Board(G3)
def verdict(bm):
    try: mv=chess.Move.from_uci(bm)
    except Exception: return "UNPARSED"
    if mv in b3.legal_moves and mv not in b1.legal_moves: return "CORRECT (game3)"
    if mv in b1.legal_moves and mv not in b3.legal_moves: return "WRONG (game1)"
    return "ambiguous (legal in both)"
def p1():
    e=Engine(EXE,options=PC20_LINES,timeout=300); e.start()
    try:
        e.position(fen=G1)
        e.send("position fen "+BAD); e.send("isready"); e.read_until("readyok")
        e.send("position fen "+G3); e.send("isready"); e.read_until("readyok")
        _,bm,_=e.go("go softnodes 2000"); return bm
    finally: e.quit()
def p2():
    e=Engine(EXE,options=PC20_LINES,timeout=300); e.start()
    try:
        for fen in (G1,BAD,G3):
            e.send("ucinewgame"); e.send("isready"); e.read_until("readyok")
            e.send("position fen "+fen); e.send("isready"); e.read_until("readyok")
        _,bm,_=e.go("go softnodes 2000"); return bm
    finally: e.quit()
def p3():
    # fresh process per game: the last process only ever sees G3
    e=Engine(EXE,options=PC20_LINES,timeout=300); e.start()
    try:
        e.position(fen=G3)
        _,bm,_=e.go("go softnodes 2000"); return bm
    finally: e.quit()
print(f"build {BUILD}  PC20, Threads 1  (correct answer must be legal in game 3 only)\n")
for name,fn in (("P1 no defence",p1),("P2 ucinewgame before each position",p2),("P3 fresh process per game",p3)):
    bm=fn()
    ok = verdict(bm).startswith("CORRECT")
    print(f"  {name:38} bestmove {str(bm):6} -> {verdict(bm):22} {'PASS' if ok else 'FAIL'}")
