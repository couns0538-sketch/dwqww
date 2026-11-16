#!/usr/bin/env python3
"""ep_capture_real.py EXE BUILD — is an en-passant capture actually GENERATED and found,
not just accepted in the FEN? Compares perft and checks the ep move appears in a divide."""
import os,re,sys
sys.path.insert(0,'/agent/repos/dwqww/forge-combo29/swarm/11')
import chess
from ucio import Engine
from pc20 import PC20_LINES
EXE=sys.argv[1]; BUILD=sys.argv[2] if len(sys.argv)>2 else "?"
# white pawn e5, black pawn just played d7-d5 => ep square d6
CASES=[
 ("ep capture available", "rnbqkbnr/ppp1pppp/8/3pP3/8/8/PPPP1PPP/RNBQKBNR w KQkq d6 0 3"),
 ("ep available, pin-ish","4k3/8/8/2pP4/8/8/8/4K3 w - c6 0 1"),
]
def divide(fen,depth=1):
    e=Engine(EXE,options=PC20_LINES,timeout=300); e.start()
    try:
        _,r=e.position(fen=fen)
        if r: return None,None,None
        e.send(f"go perft {depth}")
        lines=e.read_until("nodes ",timeout=60)
        moves=[]; total=None
        for l in lines:
            m=re.match(r"([a-h][1-8][a-h][1-8][qrbn]?): (\d+)",l)
            if m: moves.append(m.group(1))
            m2=re.match(r"nodes (\d+)",l)
            if m2: total=int(m2.group(1))
        return moves,total,None
    finally: e.quit()
print(f"build {BUILD}  PC20, Threads 1\n")
for label,fen in CASES:
    b=chess.Board(fen)
    eng_moves,eng_total,_=divide(fen)
    if eng_moves is None: print(f"  {label}: REFUSED"); continue
    py_moves=sorted(m.uci() for m in b.legal_moves)
    ep=chess.Move.from_uci("e5d6") if "e5d6" in py_moves else (chess.Move.from_uci("d5c6") if "d5c6" in py_moves else None)
    print(f"  {label}")
    print(f"    engine perft1 {eng_total}, python-chess {b.legal_moves.count()}, match {eng_total==b.legal_moves.count()}")
    if ep:
        print(f"    ep move {ep.uci()}: in python-chess {ep.uci() in py_moves}, in engine divide {ep.uci() in eng_moves}")
    else:
        print(f"    (no ep capture available in this board)")
