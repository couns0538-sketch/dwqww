#!/usr/bin/env python3
"""recovery_sweep.py EXE BUILD — is recovery automatic across many positions?
Sequence per trial: game1 -> BAD FEN -> game3(good) -> search. Count how often the answer is
legal ONLY in game3 (correct), only in game1 (infectious), or elsewhere."""
import os,re,sys
sys.path.insert(0,'/agent/repos/dwqww/forge-combo29/swarm/11')
import chess
from ucio import Engine
from pc20 import PC20_LINES
EXE=sys.argv[1]; BUILD=sys.argv[2] if len(sys.argv)>2 else "?"
BAD="4k3/8/8/8/8/8/8/4K3 w - -"
GAME1="r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq - 3 3"
fens=[]
with open("positions/G_set_G.epd") as f:
    for line in f:
        line=line.strip()
        if not line or line.startswith("#"): continue
        x=line.split(";")[0].strip().split(" ")[:6]
        if len(x)==6: fens.append(" ".join(x))
        if len(fens)>=20: break
b1=chess.Board(GAME1)
ok=infect=other=0; det=[]
for fen in fens:
    e=Engine(EXE,options=PC20_LINES,timeout=300); e.start()
    try:
        _,r=e.position(fen=GAME1)
        if r: continue
        e.send("position fen "+BAD); e.send("isready"); e.read_until("readyok")
        e.send("position fen "+fen); e.send("isready")
        ref=[l for l in e.read_until("readyok") if "invalid" in l]
        if ref: det.append((fen,"game3 refused")); continue
        infos,bm,_=e.go("go softnodes 2000")
        b3=chess.Board(fen)
        try: mv=chess.Move.from_uci(bm)
        except Exception: other+=1; continue
        in3 = mv in b3.legal_moves; in1 = mv in b1.legal_moves
        if in3 and not in1: ok+=1
        elif in1 and not in3: infect+=1; det.append((fen,"INFECTED"))
        else: other+=1; det.append((fen,f"ambiguous in3={in3} in1={in1}"))
    finally: e.quit()
print(f"build {BUILD}  PC20, Threads 1, softnodes 2000, {len(fens)} trials")
print(f"  recovered correctly (legal only in game3): {ok}")
print(f"  INFECTED (legal only in game1):            {infect}")
print(f"  ambiguous/other:                           {other}")
for d in det[:5]: print("   ",d)
