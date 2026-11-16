#!/usr/bin/env python3
"""fen_on_real_path.py EXE BUILD — the stale-board defect on the PC's ACTUAL search path.
Uses `go softnodes 2000` (the self-play setting) instead of `go depth`, PC20, Threads 1."""
import os,re,sys
sys.path.insert(0,'/agent/repos/dwqww/forge-combo29/swarm/11')
import chess
from ucio import Engine
from pc20 import PC20_LINES
EXE=sys.argv[1]; BUILD=sys.argv[2] if len(sys.argv)>2 else "?"
GAME1="r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq - 3 3"
TRUNC="4k3/8/8/8/8/8/8/4K3 w - -"
def flow(go):
    e=Engine(EXE,options=PC20_LINES,timeout=300); e.start()
    try:
        _,r=e.position(fen=GAME1)
        if r: return ("GAME1 REFUSED",r)
        e.send("position fen "+TRUNC); e.send("isready"); sync=e.read_until("readyok")
        ref=[l for l in sync if "invalid" in l]
        infos,bm,_=e.go(go)
        return (bm, ref, len(infos))
    finally: e.quit()
b1=chess.Board(GAME1); b2=chess.Board("4k3/8/8/8/8/8/8/4K3 w - - 0 1")
print(f"build {BUILD}  PC20, Threads 1\nGAME1 (Black to move): {GAME1}\ntruncated FEN sent as game 2: {TRUNC}\n")
for go in ("go softnodes 2000","go nodes 20000","go movetime 100"):
    bm,ref,ninfo=flow(go)
    if isinstance(bm,str) and bm.startswith("GAME1"): print(f"  {go:20} {bm}"); continue
    mv=chess.Move.from_uci(bm)
    which = "GAME 1 (STALE!)" if (mv in b1.legal_moves and mv not in b2.legal_moves) else ("game2 ok" if mv in b2.legal_moves else "neither")
    print(f"  {go:20} bestmove={bm}  -> {which}   refusal_seen={bool(ref)}")
