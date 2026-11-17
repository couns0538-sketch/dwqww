#!/usr/bin/env python3
"""move_quality.py : is the base's 0-node move objectively worse than the PC's searched move?"""
import re, subprocess
import chess
INFO=re.compile(r"^info depth (\d+) .*?score (cp|mate) (-?\d+)")
PC="/home/ubuntu/pcbuild/forge"
OPTS=[l.strip() for l in open("pc20_opts.txt") if l.strip() and not l.startswith("#")]+["setoption name OwnBook value false"]
FEN="rn3rk1/pp2bpp1/1q2pnbp/3p4/N2P1B1P/4P1N1/PP1Q1PP1/2R1KB1R b K - 11 16"

def score(moves=None, depth=16):
    p=subprocess.Popen([PC],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,bufsize=1)
    p.stdin.write("uci\n");p.stdin.flush()
    names=set()
    while True:
        l=p.stdout.readline()
        if not l: raise RuntimeError("died")
        s=l.strip()
        if s.startswith("option name "): names.add(s.split("option name ")[1].split(" type ")[0])
        if s=="uciok": break
    for line in OPTS:
        nm=line.split("name ")[1].split(" value ")[0]
        if nm not in names: raise RuntimeError("STOP "+nm)
        p.stdin.write(line+"\n");p.stdin.flush()
        p.stdin.write("isready\n");p.stdin.flush()
        while p.stdout.readline().strip()!="readyok": pass
    p.stdin.write("ucinewgame\n");p.stdin.flush()
    p.stdin.write("position fen "+FEN+"\n");p.stdin.flush()
    p.stdin.write("isready\n");p.stdin.flush()
    while p.stdout.readline().strip()!="readyok": pass
    cmd="go depth %d"%depth
    if moves: cmd+=" searchmoves "+" ".join(moves)
    p.stdin.write(cmd+"\n");p.stdin.flush()
    last=None;bm=None
    while True:
        l=p.stdout.readline()
        if not l: break
        s=l.strip()
        m=INFO.match(s)
        if m: last=(m.group(2),int(m.group(3)))
        if s.startswith("bestmove"): bm=s.split()[1]; break
    p.stdin.write("quit\n");p.stdin.flush()
    try: p.wait(timeout=10)
    except: p.kill()
    return last,bm

print("position:",FEN,"(black to move, base played e6e5, PC played b6b4)")
print()
print("| query | score | bestmove |")
print("|---|---|---|")
last,bm=score(); print("| unrestricted depth 16 | %s %d | %s |"%(last[0],last[1],bm))
for mv in ("e6e5","b6b4"):
    last,bm=score([mv]); print("| only %s | %s %d | %s |"%(mv,last[0],last[1],bm))
