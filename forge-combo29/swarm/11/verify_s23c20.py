#!/usr/bin/env python3
"""verify_s23c20.py EXE BUILD — seat 11 checking seat 23's C20, which refutes my S-F53.
Their claim: on five openings the two forms agree on only 3 of 5; London gives c2c4 4532 (FEN) vs
3336 (moves), Ruy Lopez gives b4f8 (FEN) vs f1b5 (moves); cause is move HISTORY, isolated by
en-passant square. Written from their sentence; their scripts not read."""
import sys,re
sys.path.insert(0,'/agent/repos/dwqww/forge-combo29/swarm/11')
import chess
from ucio import Engine
from pc20 import PC20_LINES
EXE=sys.argv[1]; BUILD=sys.argv[2] if len(sys.argv)>2 else "?"
# the two openings they name specifically
CASES=[
 ("London System",  "d2d4 g8f6 g1f3 d7d5 c1f4 c7c5 e2e3 b8c6 c2c3 d8b6"),
 ("Ruy Lopez",      "e2e4 e7e5 g1f3 b8c6 f1b5 a7a6 b5a4 g8f6 e1g1 f8e7"),
 ("Sicilian",       "e2e4 c7c5 g1f3 d7d6 d2d4 c5d4 f3d4 g8f6 b1c3 a7a6"),
 ("QGD",            "d2d4 d7d5 c2c4 e7e6 b1c3 g8f6 c1g5 f8e7 e2e3 e8g8"),
 ("capture line",   "e2e4 d7d5 e4d5 d8d5 b1c3 d5a5 d2d4 g8f6 g1f3 c8f5"),
]
def run(fen=None, moves=None):
    e=Engine(EXE,options=PC20_LINES,timeout=180); e.start()
    try:
        if moves is not None:
            e.send("position startpos moves "+" ".join(moves)); e.send("isready")
        else:
            e.send("position fen "+fen); e.send("isready")
        if [l for l in e.read_until("readyok") if "invalid" in l or "illegal" in l]:
            return ("REFUSED",)
        infos,bm,_=e.go("go softnodes 2000",timeout=60)
        n=0
        for l in infos:
            m=re.search(r"nodes (\d+)",l)
            if m: n=int(m.group(1))
        return (bm,n)
    finally: e.quit()
print(f"build {BUILD}  PC20, Threads 1, go softnodes 2000\n{'opening':16} {'via fen':>16} {'via moves':>16}  agree")
same=0
for label,mv in CASES:
    ms=mv.split()
    b=chess.Board()
    for m in ms: b.push(chess.Move.from_uci(m))
    fen=b.fen()
    a=run(fen=fen); c=run(moves=ms)
    eq=(a==c); same+=eq
    print(f"{label:16} {str(a):>16} {str(c):>16}  {'yes' if eq else 'NO'}")
print(f"\n  agree on {same} of {len(CASES)}  (seat 23 reported 3 of 5)")
