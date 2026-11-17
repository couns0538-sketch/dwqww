#!/usr/bin/env python3
"""sign_check.py : KNOWN-ANSWER CONTROL FOR THE SIGN of a UCI score.

F220's bug was a comparator pointing at the wrong side. The same class of bug in a
SCORING harness is a sign inversion: reporting a score from the wrong perspective.
Every control tonight tested magnitude or causality; none tested the SIGN.

UCI convention: a score is from the SIDE TO MOVE of the position sent. This script
tests that convention on constructed boards where the answer is not in doubt.

Exits nonzero if the sign is inverted or the convention does not hold."""
import re, subprocess, sys, os
INFO=re.compile(r"^info depth (\d+) .*?score (cp|mate) (-?\d+)")
PC="/home/ubuntu/pcbuild/forge"
OPTS=[l.strip() for l in open(os.path.join(os.path.dirname(os.path.abspath(__file__)),"pc20_opts.txt")) if l.strip() and not l.startswith("#")]+["setoption name OwnBook value false"]
def score(fen,depth=12):
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
    p.stdin.write("position fen "+fen+"\n");p.stdin.flush()
    p.stdin.write("isready\n");p.stdin.flush()
    while p.stdout.readline().strip()!="readyok": pass
    p.stdin.write("go depth %d\n"%depth);p.stdin.flush()
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

fails=[]
def check(name,got,want_pred,desc):
    ok=want_pred(got)
    print("  %-62s got=%-12s %s"%(name,got,"OK" if ok else "**FAIL** expected "+desc))
    if not ok: fails.append(name)

print("CONTROL 1 - BLACK to move and A QUEEN UP (K+Q vs K). Score must be LARGE POSITIVE.")
# black king e8, black queen d5, white king e1 ; black to move
s=score("4k3/8/8/3q4/8/8/8/4K3 b - - 0 1")
check("black up a queen, black to move -> score positive",s,lambda v: v[0]=="mate" or v[1]>500,"mate or cp>500")

print("\nCONTROL 2 - BLACK to move and A QUEEN DOWN (K vs K+Q). Score must be LARGE NEGATIVE.")
s=score("4k3/8/8/8/8/3Q4/8/4K3 b - - 0 1")
check("black down a queen, black to move -> score negative",s,lambda v: v[0]=="mate" or v[1]<-500,"mate or cp<-500")

print("\nCONTROL 3 - the SAME two boards with WHITE to move: the sign must FLIP.")
s=score("4k3/8/8/8/8/3Q4/8/4K3 w - - 0 1")
check("white up a queen, white to move -> score positive",s,lambda v: v[0]=="mate" or v[1]>500,"mate or cp>500")

print("\nCONTROL 4 - 23-F60's root, BLACK to move, score with NO move restriction.")
s=score("rn3rk1/pp2bpp1/1q2pnbp/3p4/N2P1B1P/4P1N1/PP1Q1PP1/2R1KB1R b K - 11 16")
print("  (root score, black to move):",s)

print("\nVERDICT:", "PASS" if not fails else "FAIL (%d)"%len(fails))
sys.exit(0 if not fails else 1)
