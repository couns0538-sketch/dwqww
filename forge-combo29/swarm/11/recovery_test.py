#!/usr/bin/env python3
"""recovery_test.py EXE BUILD — is the stale-board damage CONFINED to the bad FEN, or infectious?
Sequence: game1 (good) -> BAD FEN -> game3 (good, both `position fen` and `position startpos moves`).
If game 3 plays correctly, the damage is confined to the one rejected command."""
import os,re,sys
sys.path.insert(0,'/agent/repos/dwqww/forge-combo29/swarm/11')
import chess
from ucio import Engine
from pc20 import PC20_LINES
EXE=sys.argv[1]; BUILD=sys.argv[2] if len(sys.argv)>2 else "?"
GAME1="r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq - 3 3"
BAD="4k3/8/8/8/8/8/8/4K3 w - -"
GAME3_FEN="rnbqkbnr/ppp2ppp/8/3pp3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 0 3"
GAME3_MOVES="e2e4 e7e5 g1f3 d7d5"
b1=chess.Board(GAME1); b_bad=chess.Board("4k3/8/8/8/8/8/8/4K3 w - - 0 1"); b3=chess.Board(GAME3_FEN)
b3m=chess.Board(); [b3m.push(chess.Move.from_uci(m)) for m in GAME3_MOVES.split()]
def which(bm):
    try: mv=chess.Move.from_uci(bm)
    except Exception: return "UNPARSED"
    tags=[]
    if mv in b1.legal_moves: tags.append("game1")
    if mv in b_bad.legal_moves: tags.append("bad-board")
    if mv in b3.legal_moves: tags.append("game3-fen")
    if mv in b3m.legal_moves: tags.append("game3-moves")
    return ",".join(tags) if tags else "NONE-legal"
def flow(third):
    e=Engine(EXE,options=PC20_LINES,timeout=300); e.start()
    try:
        out=[]
        _,r=e.position(fen=GAME1); out.append(("game1",r is not None))
        e.send("position fen "+BAD); e.send("isready")
        ref=[l for l in e.read_until("readyok") if "invalid" in l]
        out.append(("bad-fen",bool(ref)))
        e.send(third); e.send("isready")
        ref2=[l for l in e.read_until("readyok") if "invalid" in l]
        infos,bm,_=e.go("go softnodes 2000")
        return out, bm, bool(ref2)
    finally: e.quit()
print(f"build {BUILD}  PC20, Threads 1, go softnodes 2000\ngame1: {GAME1}\nbad:   {BAD}\n")
for label,third in (("game3 as `position fen`", f"position fen {GAME3_FEN}"),
                    ("game3 as `position startpos moves ...`", f"position startpos moves {GAME3_MOVES}")):
    seq,bm,ref2=flow(third)
    print(f"  {label}")
    print(f"    sequence: {seq}, 3rd command refused={ref2}")
    print(f"    bestmove={bm}  legal-in: {which(bm)}")
