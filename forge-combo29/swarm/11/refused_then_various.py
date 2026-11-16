#!/usr/bin/env python3
"""refused_then_various.py EXE BUILD — after a refused FEN, what do the various follow-up commands
do on the PC's path? Establishes exactly which follow-ups are safe and which leak the stale board."""
import os,re,sys
sys.path.insert(0,'/agent/repos/dwqww/forge-combo29/swarm/11')
import chess
from ucio import Engine
from pc20 import PC20_LINES
EXE=sys.argv[1]; BUILD=sys.argv[2] if len(sys.argv)>2 else "?"
G1="r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq - 3 3"
BAD="4k3/8/8/8/8/8/8/4K3 w - -"
b1=chess.Board(G1)
def which(bm):
    try: mv=chess.Move.from_uci(bm)
    except Exception: return "UNPARSED"
    return "GAME1(stale)" if mv in b1.legal_moves else "other"
FOLLOWUPS=[
 ("go softnodes 2000",              ["go softnodes 2000"]),
 ("ucinewgame then go",             ["@ucinewgame","go softnodes 2000"]),
 ("isready then go",                ["@isready","go softnodes 2000"]),
 ("go perft 1",                     ["go perft 1"]),
 ("eval then go",                   ["@eval","go softnodes 2000"]),
 ("stop then go",                   ["@stop","go softnodes 2000"]),
]
print(f"build {BUILD}  PC20, Threads 1\nAfter refusing {BAD} while holding {G1}\n")
for label,cmds in FOLLOWUPS:
    e=Engine(EXE,options=PC20_LINES,timeout=300); e.start()
    try:
        e.position(fen=G1)
        e.send("position fen "+BAD); e.send("isready"); ref=[l for l in e.read_until("readyok") if "invalid" in l]
        bm="(none)"; perft=None
        for c in cmds:
            if c=="@ucinewgame": e.send("ucinewgame"); e.send("isready"); e.read_until("readyok")
            elif c=="@isready": e.send("isready"); e.read_until("readyok")
            elif c=="@eval":
                e.send("eval"); e.send("isready"); e.read_until("readyok")
            elif c=="@stop": e.send("stop")
            elif c.startswith("go perft"):
                e.send(c); lines=e.read_until("nodes ")
                for l in lines:
                    m=re.match(r"nodes (\d+)",l)
                    if m: perft=int(m.group(1))
            else:
                infos,bm,_=e.go(c)
    finally: e.quit()
    detail = f"perft1={perft}" if perft is not None else f"bm={bm} {which(bm)}"
    print(f"  {label:24} refused={bool(ref)}  {detail}")
