#!/usr/bin/env python3
"""incheck_sweep.py EXE BUILD — random positions where the side to move is in check.
Bounded generator (restarts on game end, capped iterations). Verifies evasions == python-chess
and bestmove legal, on PC20, Threads 1."""
import os,re,sys,random
sys.path.insert(0,'/agent/repos/dwqww/forge-combo29/swarm/11')
import chess
from ucio import Engine
from pc20 import PC20_LINES
EXE=sys.argv[1]; BUILD=sys.argv[2] if len(sys.argv)>2 else "?"
rng=random.Random(1101)
checked=[]; iters=0
while len(checked)<15 and iters<200000:
    iters+=1
    b=chess.Board(); 
    for _ in range(rng.randrange(1,4)):            # short walk from start, then test
        lm=list(b.legal_moves)
        if not lm: break
        b.push(rng.choice(lm))
    if b.is_check() and b.legal_moves.count()>0 and not b.is_game_over(claim_draw=False):
        checked.append(b.fen())
print(f"build {BUILD}  PC20, Threads 1 — {len(checked)} in-check positions (iters {iters})\n")
bad=0; tested=0
for fen in checked:
    e=Engine(EXE,options=PC20_LINES,timeout=180); e.start()
    try:
        _,r=e.position(fen=fen)
        if r: print(f"  REFUSED {fen[:50]}"); continue
        e.send("go perft 1"); lines=e.read_until("nodes ")
        n=None
        for l in lines:
            m=re.match(r"nodes (\d+)",l)
            if m: n=int(m.group(1))
        b2=chess.Board(fen); py=b2.legal_moves.count()
        infos,bm,_=e.go("go softnodes 2000")
        legal = (bm=="0000" and py==0) or (bm and bm!="0000" and chess.Move.from_uci(bm) in b2.legal_moves)
        tested+=1
        if n!=py or not legal:
            bad+=1; print(f"  PROBLEM {fen[:44]} engine={n} py={py} bm={bm} legal={legal}")
    finally: e.quit()
print(f"  tested {tested}, problems {bad}")
