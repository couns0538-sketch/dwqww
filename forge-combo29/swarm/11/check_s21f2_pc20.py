#!/usr/bin/env python3
"""check_s21f2_pc20.py EXE BUILD — 21-F2 on the PC build: does a REFUSED FEN leave a stale board?"""
import os,sys
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import chess
from ucio import Engine
from pc20 import PC20_LINES, describe
EXE=sys.argv[1]; BUILD=sys.argv[2] if len(sys.argv)>2 else "?"
OLD="r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq - 3 3"
REFUSED="4k3/8/8/8/8/8/8/3KK3 w - - 0 1"     # two white kings: refused
ACCEPTED="r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 3 3"
def run(target):
    e=Engine(EXE,options=PC20_LINES,timeout=180); e.start()
    try:
        _,r=e.position(fen=OLD)
        if r: raise SystemExit(f"OLD refused: {r}")
        e.send(f"position fen {target}"); e.send("isready")
        sync=e.read_until("readyok")
        info=[l for l in sync if "invalid" in l or "illegal" in l]
        _,bm,_=e.go("go depth 5")
        return bm, info
    finally: e.quit()
def side(bm,fen):
    b=chess.Board(fen)
    try: mv=chess.Move.from_uci(bm)
    except Exception: return "UNPARSED"
    if mv not in b.legal_moves: return "ILLEGAL-here"
    p=b.piece_at(mv.from_square)
    return "White" if p and p.color else "Black"
print(f"build {BUILD}\nsettings {describe()}\n")
bm1,inf1=run(REFUSED); bm2,inf2=run(ACCEPTED)
print(f"  refused FEN  -> bestmove {bm1:6} mover_in_OLD={side(bm1,OLD):12} refusal={inf1}")
print(f"  accepted FEN -> bestmove {bm2:6} mover_in_NEW={side(bm2,ACCEPTED):12} refusal={inf2}")
print(f"\n  STALE-BOARD DEFECT PRESENT: {side(bm1,OLD)=='Black'}")
