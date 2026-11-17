#!/usr/bin/env python3
"""Reproduce F61's four depths to confirm the harness and see the magnitude at each."""
import re, subprocess
import chess
INFO=re.compile(r"^info depth (\d+) .*?score (cp|mate) (-?\d+)")
PC="/home/ubuntu/pcbuild/forge"
OPTS=[l.strip() for l in open("pc20_opts.txt") if l.strip() and not l.startswith("#")]+["setoption name OwnBook value false"]
FEN="rn3rk1/pp2bpp1/1q2pnbp/3p4/N2P1B1P/4P1N1/PP1Q1PP1/2R1KB1R b K - 11 16"
def score(depth,mv):
    p=subprocess.Popen([PC],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,bufsize=1)
    p.stdin.write("uci\n");p.stdin.flush();names=set()
    while True:
        l=p.stdout.readline()
        if not l: raise RuntimeError("died")
        s=l.strip()
        if s.startswith("option name "): names.add(s.split("option name ")[1].split(" type ")[0])
        if s=="uciok": break
    for line in OPTS:
        nm=line.split("name ")[1].split(" value ")[0]
        if nm not in names: raise RuntimeError("STOP "+nm)
        p.stdin.write(line+"\n");p.stdin.flush();p.stdin.write("isready\n");p.stdin.flush()
        while p.stdout.readline().strip()!="readyok": pass
    p.stdin.write("ucinewgame\n");p.stdin.flush()
    p.stdin.write("position fen "+FEN+"\n");p.stdin.flush()
    p.stdin.write("isready\n");p.stdin.flush()
    while p.stdout.readline().strip()!="readyok": pass
    p.stdin.write(("go depth %d searchmoves %s\n"%(depth,mv)));p.stdin.flush()
    last=None
    while True:
        l=p.stdout.readline()
        if not l: break
        m=INFO.match(l.strip())
        if m: last=(m.group(2),int(m.group(3)))
        if l.strip().startswith("bestmove"): break
    p.stdin.write("quit\n");p.stdin.flush()
    try: p.wait(timeout=10)
    except Exception: p.kill()
    return last
print("F61 reproduction, e6e5 alone at each depth (F61 recorded -751/-832/-805/-853):")
for d in (8,12,16,20):
    print("  depth %2d  e6e5 -> %s"%(d,score(d,"e6e5")))
