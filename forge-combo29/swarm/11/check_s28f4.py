#!/usr/bin/env python3
"""check_s28f4.py EXE BUILD — seat 11's INDEPENDENT check of seat 28's S-F4.
Claim: the 0-node root adjudication also fires on board.is_repetition(): a mate-in-one reached a
third time by legal moves answers f2f3/cp 0/0 nodes where the SAME board given by position fen
answers a1a8/mate 1/126 nodes. Written from that sentence; seat 28's scripts not read."""
import sys
sys.path.insert(0,'/agent/repos/dwqww/forge-combo29/swarm/11')
import chess
from ucio import Engine
# a position with a mate in 1 that we can reach a third time by reversible moves
BASE="6k1/5ppp/8/8/8/8/5PPP/3Q2K1 w - - 0 1"
CYCLE=["d1d2","g8h8","d2d1","h8g8"]      # reversible, returns to BASE
def probe(fen=None, moves=None):
    e=Engine(sys.argv[1],options=[],timeout=180); e.start()
    try:
        if moves is not None:
            e.send("position startpos moves "+" ".join(moves))
        else:
            e.send("position fen "+fen)
        e.send("isready"); sync=e.read_until("readyok")
        if [l for l in sync if "invalid" in l or "illegal" in l]:
            return ("REFUSED",)
        infos,bm,_=e.go("go depth 8",timeout=60)
        n=0; sc=None
        for l in infos:
            import re
            m=re.search(r"nodes (\d+)",l)
            if m: n=int(m.group(1))
            ms=re.search(r"score (cp|mate) (-?\d+)",l)
            if ms: sc=ms.groups()
        return (bm,n,sc,len(infos))
    finally: e.quit()
# reach BASE from startpos is not trivial; instead build the repetition via fen + cycle
print(f"build {sys.argv[2] if len(sys.argv)>2 else '?'}  Threads 1, depth 8\n")
# path: from BASE via 2 full cycles -> third occurrence of BASE
mv = CYCLE + CYCLE
e=Engine(sys.argv[1],options=[],timeout=180); e.start()
try:
    e.send("position fen "+BASE); e.send("isready"); e.read_until("readyok")
finally: e.quit()
r_fen = probe(fen=BASE)
e=Engine(sys.argv[1],options=[],timeout=180); e.start()
try:
    e.send("position fen "+BASE+" moves "+" ".join(mv)); e.send("isready")
    sync=e.read_until("readyok")
    infos,bm,_=e.go("go depth 8",timeout=60)
    import re
    n=0; sc=None
    for l in infos:
        m=re.search(r"nodes (\d+)",l)
        if m: n=int(m.group(1))
        ms=re.search(r"score (cp|mate) (-?\d+)",l)
        if ms: sc=ms.groups()
    r_rep=(bm,n,sc,len(infos))
finally: e.quit()
print(f"  same board via position fen            : {r_fen}")
print(f"  same board 3rd occurrence by move list : {r_rep}")
print(f"\n  seat 28's claim (0 nodes + cp 0 for the repetition route only):", r_rep[1]==0 if r_rep else "?")
