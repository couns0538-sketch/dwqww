#!/usr/bin/env python3
"""history_move_diff.py EXE BUILD — hunt for a case where HISTORY ALONE changes the MOVE,
with the board identical. Sweeps several openings x occurrence counts."""
import sys,re
sys.path.insert(0,'/agent/repos/dwqww/forge-combo29/swarm/11')
import chess
from ucio import Engine
from pc20 import PC20_LINES
EXE=sys.argv[1]; BUILD=sys.argv[2] if len(sys.argv)>2 else "?"
OPENINGS=[
 ("London","d2d4 g8f6 g1f3 d7d5 c1f4 c7c5 e2e3 b8c6"),
 ("QGD","d2d4 d7d5 c2c4 e7e6 b1c3 g8f6 c1g5 f8e7"),
 ("KID","d2d4 g8f6 c2c4 g7g6 b1c3 f8g7 e2e4 d7d6"),
 ("English","c2c4 e7e5 b1c3 g8f6 g2g3 d7d5 c4d5 f6d5"),
 ("Sicilian","e2e4 c7c5 g1f3 d7d6 d2d4 c5d4 f3d4 g8f6"),
 ("Nimzo","d2d4 g8f6 c2c4 e7e6 b1c3 f8b4 e2e3 e8g8"),
]
def run(fen=None, moves=None):
    e=Engine(EXE,options=PC20_LINES,timeout=180); e.start()
    try:
        if moves is not None:
            e.send("position startpos moves "+" ".join(moves)); e.send("isready")
        else:
            e.send("position fen "+fen); e.send("isready")
        if [l for l in e.read_until("readyok") if "invalid" in l or "illegal" in l]:
            return None
        infos,bm,_=e.go("go softnodes 2000",timeout=60)
        n=0
        for l in infos:
            m=re.search(r"nodes (\d+)",l)
            if m: n=int(m.group(1))
        return (bm,n)
    finally: e.quit()
def shuttle(b):
    """a reversible 4-ply cycle that returns to the same board"""
    for mv in ("g1f3","g8f6","f3g1","f6g8"):
        try:
            m=chess.Move.from_uci(mv)
            if m in b.legal_moves: b.push(m)
            else: return None
        except Exception: return None
    return b
print(f"build {BUILD}  PC20, Threads 1, softnodes 2000\n{'opening':12} {'fen':>14} {'moves x1':>14} {'moves x2':>14} {'move differs?':>14}")
found=0
for label,seq in OPENINGS:
    ms=seq.split(); b=chess.Board()
    ok=True
    for m in ms:
        mv=chess.Move.from_uci(m)
        if mv not in b.legal_moves: ok=False; break
        b.push(mv)
    if not ok: print(f"{label:12} (illegal sequence, skipped)"); continue
    fen=b.fen()
    a=run(fen=fen); c1=run(moves=ms)
    b2=b.copy(); s=shuttle(b2)
    c2=run(moves=ms+["g1f3","g8f6","f3g1","f6g8"]) if s is not None else None
    diff = (a and c1 and a[0]!=c1[0]) or (a and c2 and a[0]!=c2[0])
    if diff: found+=1
    print(f"{label:12} {str(a):>14} {str(c1):>14} {str(c2):>14} {'*** MOVE DIFFERS' if diff else 'same move'}")
print(f"\n  openings where history alone changed the MOVE: {found} of {len(OPENINGS)}")
