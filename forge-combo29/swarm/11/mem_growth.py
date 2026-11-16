#!/usr/bin/env python3
"""mem_growth.py EXE BUILD — proper memory measurement, replacing the failed RSS attempt in S-F88.
Reads /proc/<pid>/status VmRSS directly, over many games in ONE long-lived process."""
import os,re,sys,time,random
sys.path.insert(0,'/agent/repos/dwqww/forge-combo29/swarm/11')
import chess
from ucio import Engine
from pc20 import PC20_LINES
EXE=sys.argv[1]; BUILD=sys.argv[2] if len(sys.argv)>2 else "?"
GAMES=120
def rss_mb(pid):
    try:
        for line in open(f"/proc/{pid}/status"):
            if line.startswith("VmRSS:"):
                return int(line.split()[1])/1024.0
    except Exception:
        return None
    return None
rng=random.Random(1101)
e=Engine(EXE,options=PC20_LINES,timeout=300); e.start()
pid=e.proc.pid
samples=[]
print(f"build {BUILD}  PC20, Threads 1, {GAMES} games in ONE process (pid {pid})\n")
illegal=0
for g in range(1,GAMES+1):
    b=chess.Board(); moves=[]
    for _ in range(rng.randrange(6,40)):
        lm=list(b.legal_moves)
        if not lm or b.is_game_over(claim_draw=False): break
        m=rng.choice(lm); b.push(m); moves.append(m.uci())
    e.send("position startpos moves "+" ".join(moves)); e.send("isready"); e.read_until("readyok")
    infos,bm,_=e.go("go nodes 50000")
    if bm and bm!="0000":
        try:
            if chess.Move.from_uci(bm) not in b.legal_moves: illegal+=1
        except Exception: pass
    if g % 15 == 0 or g==1:
        r=rss_mb(pid); samples.append((g,r))
        print(f"  after game {g:3}: VmRSS {r:.1f} MB" if r else f"  after game {g:3}: RSS unreadable")
e.send("quit")
try: e.proc.wait(timeout=5)
except Exception: e.proc.kill()
vals=[r for _,r in samples if r]
print(f"\n  games {GAMES}, illegal {illegal}")
if len(vals)>=2:
    print(f"  RSS first {vals[0]:.1f} MB -> last {vals[-1]:.1f} MB, growth {vals[-1]-vals[0]:+.1f} MB")
    print(f"  (Hash 16 MB is preallocated, so a flat curve is the expected shape)")
else:
    print("  RSS SAMPLING FAILED - no claim made")
