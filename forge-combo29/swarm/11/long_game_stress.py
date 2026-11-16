#!/usr/bin/env python3
"""long_game_stress.py EXE BUILD — one long process, many games, growing move lists.
Checks for memory growth, slowdown, or state leak across 40 games in ONE process (vs the correct
one-process-per-game protocol). PC20, Threads 1."""
import os,re,sys,time,random,resource
sys.path.insert(0,'/agent/repos/dwqww/forge-combo29/swarm/11')
import chess
from ucio import Engine
from pc20 import PC20_LINES
EXE=sys.argv[1]; BUILD=sys.argv[2] if len(sys.argv)>2 else "?"
GAMES=40
rng=random.Random(1101)
e=Engine(EXE,options=PC20_LINES,timeout=300); e.start()
times=[]; illegal=0
print(f"build {BUILD}  PC20, Threads 1, {GAMES} games in ONE process, go nodes 20000\n")
for g in range(1,GAMES+1):
    b=chess.Board(); moves=[]
    for _ in range(rng.randrange(6,30)):
        lm=list(b.legal_moves)
        if not lm or b.is_game_over(claim_draw=False): break
        m=rng.choice(lm); b.push(m); moves.append(m.uci())
    _,r=e.position(fen=None)
    if r: continue
    # send the move list form (growing path a GUI uses)
    e.send("position startpos moves "+" ".join(moves)); e.send("isready"); e.read_until("readyok")
    t0=time.monotonic()
    infos,bm,_=e.go("go nodes 20000")
    times.append((time.monotonic()-t0)*1000)
    if bm and bm!="0000" and chess.Move.from_uci(bm) not in b.legal_moves: illegal+=1
rss=resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss/1024
e.quit()
first=sum(times[:10])/10; last=sum(times[-10:])/10
print(f"  moves searched {len(times)}, illegal {illegal}")
print(f"  first 10 games avg {first:.0f} ms, last 10 avg {last:.0f} ms (ratio {last/first:.2f}x)")
print(f"  child process peak RSS {rss:.0f} MB")
