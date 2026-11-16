#!/usr/bin/env python3
"""full_game_hazard.py EXE BUILD — play a real game move by move (engine vs itself) on the PC's
self-play setting, and inject ONE malformed FEN mid-game to show the concrete cost."""
import os,re,sys
sys.path.insert(0,'/agent/repos/dwqww/forge-combo29/swarm/11')
import chess
from ucio import Engine
from pc20 import PC20_LINES
EXE=sys.argv[1]; BUILD=sys.argv[2] if len(sys.argv)>2 else "?"
def ask(fen):
    e=Engine(EXE,options=PC20_LINES,timeout=300); e.start()
    try:
        _,r=e.position(fen=fen)
        if r: return None,r
        infos,bm,_=e.go("go softnodes 2000")
        return bm,None
    finally: e.quit()
print(f"build {BUILD}  PC20, Threads 1, go softnodes 2000\n")
b=chess.Board()
fens=[]
for ply in range(12):
    bm,err=ask(b.fen())
    if err or not bm or bm=="0000": print(f"  ply {ply}: stopped ({err or bm})"); break
    b.push(chess.Move.from_uci(bm)); fens.append(bm)
print(f"  normal 12-ply game: {b.fen()}")
print(f"  moves: {' '.join(fens)}")
# now the hazard: take the position after 6 plies, send a TRUNCATED fen, then ask
b6=chess.Board()
for m in fens[:6]: b6.push(chess.Move.from_uci(m))
e=Engine(EXE,options=PC20_LINES,timeout=300); e.start()
try:
    # engine has the 6-ply board, then we send a truncated FEN for a NEW game
    _,r=e.position(fen=b6.fen())
    e.send("position fen 8/8/8/8/8/8/8/K6k w - -")   # truncated (5 fields)
    e.send("isready"); ref=[l for l in e.read_until("readyok") if "invalid" in l]
    infos,bm,_=e.go("go softnodes 2000")
finally: e.quit()
mv=chess.Move.from_uci(bm)
print(f"\n  HAZARD: after the 6-ply board, sent a 5-field FEN -> refusal={bool(ref)}")
print(f"    bestmove {bm}: legal in the 6-ply board = {mv in b6.legal_moves}; "
      f"legal in the intended new board = {mv in chess.Board('8/8/8/8/8/8/8/K6k w - - 0 1').legal_moves}")
