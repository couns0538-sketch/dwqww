#!/usr/bin/env python3
"""defence_protocol2.py — the REAL dangerous pattern: the bad FEN IS game 3's position.
So there is no good position afterwards; the harness asks for a move on what it thinks is
game 3. Test which protocol prevents a wrong-game move in THAT case."""
import os,re,sys
sys.path.insert(0,'/agent/repos/dwqww/forge-combo29/swarm/11')
import chess
from ucio import Engine
from pc20 import PC20_LINES
EXE=sys.argv[1]; BUILD=sys.argv[2] if len(sys.argv)>2 else "?"
G1="r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq - 3 3"
G3_TRUNC="rnbqkbnr/ppp2ppp/8/3pp3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 0"   # missing fullmove
G3_OK="rnbqkbnr/ppp2ppp/8/3pp3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 0 3"
b1=chess.Board(G1); b3=chess.Board(G3_OK)
def verdict(bm,board):
    try: mv=chess.Move.from_uci(bm)
    except Exception: return "UNPARSED"
    in3 = mv in b3.legal_moves; in1 = mv in b1.legal_moves
    if in3 and not in1: return "CORRECT(game3)"
    if in1 and not in3: return "WRONG(game1)"
    return "ambiguous"
def run(mode):
    """mode: 'naive' asks immediately after the bad FEN; 'detect' aborts; 'fixup' ucinewgame+resend good."""
    e=Engine(EXE,options=PC20_LINES,timeout=300); e.start()
    try:
        e.position(fen=G1)
        e.send("position fen "+G3_TRUNC); e.send("isready")
        sync=e.read_until("readyok"); refused=[l for l in sync if "invalid" in l]
        if mode=="detect":
            return ("ABORTED", bool(refused))
        if mode=="fixup":
            e.send("ucinewgame"); e.send("isready"); e.read_until("readyok")
            e.send("position fen "+G3_OK); e.send("isready"); e.read_until("readyok")
        _,bm,_=e.go("go softnodes 2000")
        return (bm, bool(refused))
    finally: e.quit()
print(f"build {BUILD}  PC20, Threads 1")
print(f"game1={G1}\ngame3 sent TRUNCATED as {G3_TRUNC}\n")
for mode in ("naive","detect","fixup"):
    r=run(mode)
    if r[0]=="ABORTED":
        print(f"  {mode:8} -> harness aborted on refusal_seen={r[1]}  => no wrong move played  PASS")
    else:
        bm,ref=r
        print(f"  {mode:8} -> bestmove {bm} refusal_seen={ref}  {verdict(bm,G3_OK)}")
