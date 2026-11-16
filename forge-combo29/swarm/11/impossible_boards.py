#!/usr/bin/env python3
"""impossible_boards.py EXE BUILD — FENs the engine ACCEPTS that no game can reach.
File 1 says a triple check by three knights is accepted and its moves generated right.
Does the SEARCH behave correctly on such boards (real path: softnodes 2000)?"""
import os,re,sys
sys.path.insert(0,'/agent/repos/dwqww/forge-combo29/swarm/11')
import chess
from ucio import Engine
from pc20 import PC20_LINES
EXE=sys.argv[1]; BUILD=sys.argv[2] if len(sys.argv)>2 else "?"
CASES=[
 ("triple check, 3 knights", "4k3/8/8/8/8/2nnn3/8/4K3 w - - 0 1"),
 ("check from 2 knights+rook","4k3/8/8/8/8/2nnr3/8/4K3 w - - 0 1"),
 ("9 pawns white (1 promo)", "4k3/8/8/8/8/P7/PPPPPPPP/4K3 w - - 0 1"),
 ("side to move cannot have just moved (in check, no evasion)", "4k3/8/8/8/8/8/8/R3K3 b - - 0 1"),
 ("impossible ep (already tested)", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq e6 0 1"),
]
def probe(fen):
    e=Engine(EXE,options=PC20_LINES,timeout=300); e.start()
    try:
        _,r=e.position(fen=fen)
        if r: return ("REFUSED", r[0][:66])
        e.send("go perft 1"); lines=e.read_until("nodes ")
        n=None
        for l in lines:
            m=re.match(r"nodes (\d+)",l)
            if m: n=int(m.group(1))
        infos,bm,_=e.go("go softnodes 2000")
        return (n,bm,len(infos))
    finally: e.quit()
print(f"build {BUILD}  PC20, Threads 1\n")
print(f"{'case':46} {'py':>5} {'eng':>5} {'match':>6} {'bestmove':>9} {'legal':>6}")
for label,fen in CASES:
    b=chess.Board(fen) if True else None
    py=b.legal_moves.count()
    r=probe(fen)
    if r[0]=="REFUSED": print(f"{label:46} REFUSED: {r[1]}"); continue
    n,bm,ninfo=r
    try: legal = chess.Move.from_uci(bm) in b.legal_moves if bm not in ("0000",) else py==0
    except Exception: legal=False
    print(f"{label:46} {py:>5} {n:>5} {str(n==py):>6} {str(bm):>9} {str(legal):>6}")
