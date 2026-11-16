#!/usr/bin/env python3
"""clock_depth.py : does a 6s+0.06 clock reach depth 20 on the six lone-king boards? That decides whether the PC's
deeper-search repair ever fires in a PC-time-control game.
"""
import re, subprocess, time
OPTS=[l.strip() for l in open("../job7/pc20_opts.txt") if l.strip() and not l.startswith("#")]
OPTS.append("setoption name OwnBook value false")
INFO = re.compile(r"^info depth (\d+) .*?score (cp|mate) (-?\d+)")
FENS = [
 "6k1/8/7R/2K5/8/8/8/8 w - - 0 1","7K/5k2/8/4R3/8/8/8/8 w - - 0 1",
 "8/3K4/8/8/8/7k/3R4/8 w - - 0 1","4k2K/8/8/1R6/8/8/8/8 w - - 0 1",
 "8/8/8/8/8/R7/7K/3k4 w - - 0 1","8/8/8/6k1/8/8/5K2/1Q6 w - - 0 1"]
def go(exe,fen):
    p=subprocess.Popen([exe],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,bufsize=1)
    p.stdin.write("uci\n");p.stdin.flush()
    names=set()
    while True:
        l=p.stdout.readline()
        if not l: raise RuntimeError("died")
        s=l.strip()
        if s.startswith("option name "): names.add(s.split("option name ")[1].split(" type ")[0])
        if s=="uciok": break
    for line in OPTS:
        if "OwnBook" in names:
            p.stdin.write(line+"\n");p.stdin.flush()
            p.stdin.write("isready\n");p.stdin.flush()
            while p.stdout.readline().strip()!="readyok": pass
    p.stdin.write("ucinewgame\n");p.stdin.flush()
    p.stdin.write("position fen "+fen+"\n");p.stdin.flush()
    p.stdin.write("isready\n");p.stdin.flush()
    while p.stdout.readline().strip()!="readyok": pass
    t=time.monotonic()
    p.stdin.write("go wtime 6000 btime 6000 winc 60 binc 60\n");p.stdin.flush()
    last=None
    while True:
        l=p.stdout.readline()
        if not l: raise RuntimeError("died in search")
        s=l.strip()
        m=INFO.match(s)
        if m: last=(int(m.group(1)),m.group(2),int(m.group(3)))
        if s.startswith("bestmove"): break
    w=time.monotonic()-t
    p.stdin.write("quit\n");p.stdin.flush()
    try: p.wait(timeout=10)
    except: p.kill()
    return last, w
print("| # | build | depth reached | score | wall ms | reaches depth 20? |")
print("|---|---|---|---|---|---|")
for i,fen in enumerate(FENS,1):
    for name,exe in (("PC r15 + PC20","/home/ubuntu/pcbuild/forge"),):
        last,w=go(exe,fen)
        print("| %d | %s | %d | %s %d | %.0f | %s |" % (i,name,last[0],last[1],last[2],1000*w,
              "yes" if last[0]>=20 else "no"))
