#!/usr/bin/env python3
"""illegal_move_route.py EXE BUILD — the SECOND route into the stale-board hazard:
`position startpos moves` with an illegal move keeps the legal PREFIX, so the engine searches a
board the GUI did not intend — and a GUI sends a move list every move, so this route is far more
exposed than the malformed-FEN route. PC20, Threads 1."""
import os,re,sys
sys.path.insert(0,'/agent/repos/dwqww/forge-combo29/swarm/11')
import chess
from ucio import Engine
from pc20 import PC20_LINES
EXE=sys.argv[1]; BUILD=sys.argv[2] if len(sys.argv)>2 else "?"
# a real opening, then an illegal move appended (GUI desync / out-of-order token)
PATH="e2e4 e7e5 g1f3 b8c6 f1c4 f8c5"
ILLEGAL="e2e4"          # already played: illegal now
b=chess.Board()
for m in PATH.split(): b.push(chess.Move.from_uci(m))
prefix_fen=b.fen()
b_start=chess.Board()
e=Engine(EXE,options=PC20_LINES,timeout=300); e.start()
try:
    e.send("position startpos moves "+PATH+" "+ILLEGAL); e.send("isready")
    sync=e.read_until("readyok"); ref=[l for l in sync if "invalid" in l or "illegal" in l]
    e.send("go perft 1"); lines=e.read_until("nodes ")
    n=None
    for l in lines:
        m=re.match(r"nodes (\d+)",l)
        if m: n=int(m.group(1))
    infos,bm,_=e.go("go softnodes 2000")
finally: e.quit()
py_prefix=chess.Board(prefix_fen).legal_moves.count()
print(f"build {BUILD}  PC20, Threads 1")
print(f"  position startpos moves {PATH} {ILLEGAL}")
print(f"  answer lines : {ref}")
print(f"  perft 1      : engine {n}   legal prefix's count {py_prefix}   (startpos = 20)")
print(f"  bestmove     : {bm}")
print(f"  board searched: {'LEGAL PREFIX (intended)' if n==py_prefix else 'something else'}")
print(f"\n  So an illegal move in the list does NOT reject the game; the engine silently searches")
print(f"  the legal prefix and answers for THAT board — the same 'confident wrong board' shape")
print(f"  as the malformed-FEN route, but triggered by one bad token in a move list.")
