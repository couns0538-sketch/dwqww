#!/usr/bin/env python3
"""prefix_divergence.py EXE BUILD — Route 2 in a real setting: a GUI sends a growing move list and
ONE token is corrupted/out of order. How far does the searched board diverge from the intended one?
Measures: number of plies silently dropped, and whether the returned move is legal in the intended board."""
import os,re,sys
sys.path.insert(0,'/agent/repos/dwqww/forge-combo29/swarm/11')
import chess
from ucio import Engine
from pc20 import PC20_LINES
EXE=sys.argv[1]; BUILD=sys.argv[2] if len(sys.argv)>2 else "?"
GAME="e2e4 e7e5 g1f3 b8c6 f1b5 a7a6 b5a4 g8f6 e1g1 f8e7 f1e1 b7b5 a4b3 d7d6 c2c3 e8g8".split()
def probe(moves):
    e=Engine(EXE,options=PC20_LINES,timeout=300); e.start()
    try:
        e.send("position startpos moves "+" ".join(moves)); e.send("isready")
        ref=[l for l in e.read_until("readyok") if "invalid" in l or "illegal" in l]
        e.send("go perft 1"); lines=e.read_until("nodes ")
        n=None
        for l in lines:
            m=re.match(r"nodes (\d+)",l)
            if m: n=int(m.group(1))
        infos,bm,_=e.go("go softnodes 2000")
        return ref,n,bm
    finally: e.quit()
def board_after(ms):
    b=chess.Board(); ok=True
    for m in ms:
        mv=chess.Move.from_uci(m)
        if mv not in b.legal_moves: return b,False
        b.push(mv)
    return b,True
print(f"build {BUILD}  PC20, Threads 1\nintended game has {len(GAME)} plies\n")
full_board,full_ok=board_after(GAME)
ref,n,bm=probe(GAME)
print(f"  clean list      : refusals={ref} perft1={n} (py {full_board.legal_moves.count()}) bm={bm}")
print()
print(f"{'corruption':28} {'plies kept':>10} {'perft1':>7} {'py':>5} {'bm':>7} {'bm legal in intended?':>22}")
for k in (2,6,10,14):
    bad=GAME[:k]+["e2e4"]        # an already-played move => illegal here
    kept,_=board_after([m for m in bad if True])
    b_kept,ok=board_after(bad)
    ref,n,bm=probe(bad)
    try: legal = chess.Move.from_uci(bm) in full_board.legal_moves
    except Exception: legal=False
    print(f"{'illegal token at ply '+str(k+1):28} {k:>10} {str(n):>7} {b_kept.legal_moves.count():>5} {str(bm):>7} {str(legal):>22}")
