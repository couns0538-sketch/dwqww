#!/usr/bin/env python3
"""mate0_semantics.py EXE BUILD — settle the disagreement: is `score mate 0` on a checkmated root
CORRECT UCI (seat 21's withdrawal) or a defect (seat 25's S-F6, seat 20's S-C20)?
Test the full ladder: mated now, mate in 1, mate in 2, stalemate, drawn, winning."""
import sys,re
sys.path.insert(0,'/agent/repos/dwqww/forge-combo29/swarm/11')
import chess
from ucio import Engine
EXE=sys.argv[1]; BUILD=sys.argv[2] if len(sys.argv)>2 else "?"
CASES=[
 ("checkmated NOW (black)", "4R1k1/5ppp/8/8/8/8/5PPP/6K1 b - - 1 60", "mate 0 expected if UCI-correct"),
 ("mate in 1 (white)",      "6k1/5ppp/8/8/8/8/5PPP/3Q2K1 w - - 0 1",  "mate 1"),
 ("mate in 2 (white)",      "6k1/5ppp/8/8/8/8/5PPP/2Q3K1 w - - 0 1",  "mate 2 or 1"),
 ("stalemated NOW (black)", "7k/5Q2/6K1/8/8/8/8/8 b - - 0 1",         "cp 0"),
 ("dead draw",              "6k1/8/8/8/8/8/8/4K3 w - - 0 1",          "cp 0"),
 ("clear win (KQvK)",       "6k1/8/8/8/8/8/8/4QK2 w - - 0 1",         "mate N or big cp"),
]
print(f"build {BUILD}  Threads 1, depth 10\n{'case':26} {'expect':26} {'score':14} {'bm':7} {'nodes':>7}")
for label,fen,expect in CASES:
    b=chess.Board(fen)
    e=Engine(EXE,options=[],timeout=120); e.start()
    try:
        _,r=e.position(fen=fen)
        if r: print(f"{label:26} REFUSED"); continue
        infos,bm,_=e.go("go depth 10",timeout=60)
        sc=None; n=0
        for l in infos:
            m=re.search(r"score (cp|mate) (-?\d+)",l)
            if m: sc=(m.group(1),int(m.group(2)))
            mn=re.search(r"nodes (\d+)",l)
            if mn: n=int(mn.group(1))
        legal=b.legal_moves.count()
        print(f"{label:26} {expect:26} {str(sc):14} {str(bm):7} {n:>7}  (py legal {legal})")
    finally: e.quit()
print("\nUCI: `score mate y` = mate in y MOVES for the side to move. y=0 therefore means")
print("'already mated', and bestmove 0000 is the only sensible move. Seat 21's withdrawal matches that.")
