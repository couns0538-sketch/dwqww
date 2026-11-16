#!/usr/bin/env python3
"""bare_king_one_thread.py : test FORGE_FIX_BARE_KING_ONE_THREAD / LMR_CAP — file 5 says the PC fixes lone-king
endings. Seat 30's six boards are the known case; this asks the narrower question the switch names: does the PC
find mates on bare-king boards at a moderate depth where the base does not?
"""
import re, subprocess, sys
INFO = re.compile(r"^info depth (\d+) .*?score (cp|mate) (-?\d+)")

FENS = [
 "6k1/8/7R/2K5/8/8/8/8 w - - 0 1",
 "7K/5k2/8/4R3/8/8/8/8 w - - 0 1",
 "8/3K4/8/8/8/7k/3R4/8 w - - 0 1",
 "4k2K/8/8/1R6/8/8/8/8 w - - 0 1",
 "8/8/8/8/8/R7/7K/3k4 w - - 0 1",
 "8/8/8/6k1/8/8/5K2/1Q6 w - - 0 1",
]
def go(exe,fen,depth):
    p=subprocess.Popen([exe],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,bufsize=1)
    p.stdin.write("uci\n");p.stdin.flush()
    names=set()
    while True:
        l=p.stdout.readline()
        if not l: raise RuntimeError("died")
        s=l.strip()
        if s.startswith("option name "): names.add(s.split("option name ")[1].split(" type ")[0])
        if s=="uciok": break
    if "OwnBook" in names:
        p.stdin.write("setoption name OwnBook value false\n");p.stdin.flush()
        p.stdin.write("isready\n");p.stdin.flush()
        while p.stdout.readline().strip()!="readyok": pass
    p.stdin.write("ucinewgame\n");p.stdin.flush()
    p.stdin.write("position fen "+fen+"\n");p.stdin.flush()
    p.stdin.write("isready\n");p.stdin.flush()
    while p.stdout.readline().strip()!="readyok": pass
    p.stdin.write("go depth %d\n"%depth);p.stdin.flush()
    last=None
    while True:
        l=p.stdout.readline()
        if not l: raise RuntimeError("died in search")
        s=l.strip()
        m=INFO.match(s)
        if m: last=(m.group(2),int(m.group(3)))
        if s.startswith("bestmove"): break
    p.stdin.write("quit\n");p.stdin.flush()
    try: p.wait(timeout=10)
    except: p.kill()
    return last

print("| # | fen | base d12 | base d20 | base d24 | PC d12 | PC d20 | PC d24 |")
print("|---|---|---|---|---|---|---|---|")
for i,fen in enumerate(FENS,1):
    row=[]
    for exe in ("/home/ubuntu/build/forge","/home/ubuntu/pcbuild/forge"):
        for d in (12,20,24):
            r=go(exe,fen,d)
            row.append("%s %d"%(r[0],r[1]) if r else "-")
    print("| %d | %s | %s | %s | %s | %s | %s | %s |" % (i,fen,row[0],row[1],row[2],row[3],row[4],row[5]))
