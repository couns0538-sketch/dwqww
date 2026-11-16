#!/usr/bin/env python3
"""fen_moves_form.py EXE BUILD — the combined `position fen F moves ...` form on the PC's path.
Checks: legal moves applied, illegal move keeps prefix, refused FEN keeps the OLD position."""
import os,re,sys
sys.path.insert(0,'/agent/repos/dwqww/forge-combo29/swarm/11')
import chess
from ucio import Engine
from pc20 import PC20_LINES
EXE=sys.argv[1]; BUILD=sys.argv[2] if len(sys.argv)>2 else "?"
KQK="6k1/5ppp/8/8/8/8/5PPP/3Q2K1 w - - 0 1"      # 27 legal moves
OLD="r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1"        # 26 legal moves
def probe(cmd):
    e=Engine(EXE,options=PC20_LINES,timeout=300); e.start()
    try:
        e.position(fen=OLD)                      # establish a known old board
        e.send(cmd); e.send("isready"); sync=e.read_until("readyok")
        ref=[l for l in sync if "invalid" in l or "illegal" in l]
        e.send("go perft 1"); lines=e.read_until("nodes ")
        n=None
        for l in lines:
            m=re.match(r"nodes (\d+)",l)
            if m: n=int(m.group(1))
        infos,bm,_=e.go("go softnodes 2000")
        return ref,n,bm
    finally: e.quit()
cases=[
 ("legal move applied",   f"position fen {KQK} moves d1d8"),
 ("illegal move (knight)",f"position fen {KQK} moves g1f3"),
 ("2 legal moves",        f"position fen {KQK} moves d1d8 g8h8"),
 ("refused FEN + moves",  f"position fen 4k3/8/8/8/8/8/8/3KK3 w - - 0 1 moves e1e2"),
]
print(f"build {BUILD}  PC20, Threads 1\nold board has {chess.Board(OLD).legal_moves.count()} moves; {KQK} has {chess.Board(KQK).legal_moves.count()}\n")
print(f"{'case':24} {'refusal':>38} {'perft1':>7} {'bm':>7}")
for label,cmd in cases:
    ref,n,bm=probe(cmd)
    print(f"{label:24} {str(ref):>38} {str(n):>7} {str(bm):>7}")
