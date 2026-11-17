#!/usr/bin/env python3
"""verdict_check.py : if the 'root occ' column is stale (3 instead of 1), is the VERDICT
column still right? Measure the three disputed rows on the base build."""
import chess, subprocess, re
BASE="/home/ubuntu/build/forge"
INFO=re.compile(r"^info depth (\d+) .*?score (cp|mate) (-?\d+).*?nodes (\d+)")
def search(fen,moves,depth=10):
    p=subprocess.Popen([BASE],stdin=subprocess.PIPE,stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT,text=True,bufsize=1)
    def s(x): p.stdin.write(x+"\n"); p.stdin.flush()
    s("uci")
    while p.stdout.readline().strip()!="uciok": pass
    for o in ("setoption name Threads value 1","setoption name Hash value 16","setoption name OwnBook value false"):
        s(o); s("isready")
        while p.stdout.readline().strip()!="readyok": pass
    s("ucinewgame"); s("position fen %s moves %s"%(fen,moves)); s("isready")
    while p.stdout.readline().strip()!="readyok": pass
    s("go depth %d"%depth)
    last=None; bm=None
    while True:
        l=p.stdout.readline()
        if not l: break
        m=INFO.match(l.strip())
        if m: last=(m.group(2),int(m.group(3)),int(m.group(4)))
        if l.strip().startswith("bestmove"): bm=l.split()[1]; break
    s("quit")
    try: p.wait(timeout=10)
    except Exception: p.kill()
    return last,bm
ROWS=[("M7","rn1qkb1r/p2p1p2/1p2p3/2pP2pp/Q1N3P1/P1P1BP2/1P2P1K1/R4BNR w kq - 1 15","c4e5 h8g8 e5c4 g8h8 c4e5 h8g8 e5c4 g8h8",11390,"d5e6"),
      ("C1","r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 0 1","a1b1 a8b8 b1a1 b8a8 a1b1 a8b8 b1a1 b8a8",17601,"h1h8"),
      ("C1h","r3k2r/8/8/8/8/8/8/R3K2R w KQkq - 13 7","a1b1 a8b8 b1a1 b8a8 a1b1 a8b8 b1a1 b8a8",17601,"h1h8")]
print("%-5s %-8s %-8s %-9s %-9s %s"%("row","nodes","stated","move","stated","verdict column right?"))
for n,fen,mv,stated_nodes,stated_bm in ROWS:
    last,bm=search(fen,mv)
    ok = last[2]>0 and last[2]==stated_nodes and bm==stated_bm
    print("%-5s %-8d %-8d %-9s %-9s %s"%(n,last[2],stated_nodes,bm,stated_bm,"yes" if ok else "NO"))
    print("      full: %s %d | pv-head %s"%(last[0],last[1],bm))
