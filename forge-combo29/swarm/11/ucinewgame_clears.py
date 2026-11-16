#!/usr/bin/env python3
"""ucinewgame_clears.py EXE BUILD — does `ucinewgame` clear the stale board left by a refused FEN?
Determines the DEFENCE: if yes, "send ucinewgame after a refused position" suffices.
If no, only a fresh process does."""
import os,re,sys
sys.path.insert(0,'/agent/repos/dwqww/forge-combo29/swarm/11')
import chess
from ucio import Engine
from pc20 import PC20_LINES
EXE=sys.argv[1]; BUILD=sys.argv[2] if len(sys.argv)>2 else "?"
GAME1="r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq - 3 3"
TRUNC="4k3/8/8/8/8/8/8/4K3 w - -"
b1=chess.Board(GAME1); b2=chess.Board("4k3/8/8/8/8/8/8/4K3 w - - 0 1")
def label(bm):
    try: mv=chess.Move.from_uci(bm)
    except Exception: return "UNPARSED"
    in1 = mv in b1.legal_moves; in2 = mv in b2.legal_moves
    if in1 and not in2: return "GAME1 (stale)"
    if in2: return "game2/startpos-side"
    return "neither"
def scenario(with_newgame, resend=False):
    e=Engine(EXE,options=PC20_LINES,timeout=300); e.start()
    try:
        _,r=e.position(fen=GAME1)
        if r: return ("GAME1 REFUSED",)
        e.send("position fen "+TRUNC); e.send("isready"); sync=e.read_until("readyok")
        ref=[l for l in sync if "invalid" in l]
        if with_newgame:
            e.send("ucinewgame"); e.send("isready"); e.read_until("readyok")
        if resend:
            e.send("position fen "+TRUNC); e.send("isready"); e.read_until("readyok")
        infos,bm,_=e.go("go softnodes 2000")
        return (bm, bool(ref), label(bm))
    finally: e.quit()
print(f"build {BUILD}  PC20, Threads 1, go softnodes 2000")
print(f"game1 = {GAME1}\ntruncated game2 = {TRUNC}\n")
cases=[("no defence",              dict(with_newgame=False)),
       ("ucinewgame after refusal",dict(with_newgame=True)),
       ("ucinewgame + resend FEN", dict(with_newgame=True,resend=True))]
for name,kw in cases:
    r=scenario(**kw)
    if len(r)==1: print(f"  {name:26} {r[0]}"); continue
    bm,ref,lab=r
    print(f"  {name:26} bestmove={bm:6} refusal_seen={ref}  -> {lab}")
