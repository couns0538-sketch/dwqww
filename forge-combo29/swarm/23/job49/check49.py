#!/usr/bin/env python3
"""job49 : is 23-F60's losing move e6e5 index 0 in the ENGINE's own divide on the middlegame FEN?"""
import re, subprocess, sys, os
BASE=os.path.expanduser("~/build/forge")
MOVELINE=re.compile(r"^([a-h][1-8][a-h][1-8][qrbn]?): (\d+)$")
SUMMARY=re.compile(r"^nodes (\d+)$")
INFO=re.compile(r"^info depth (\d+) .*?score (cp|mate) (-?\d+).*?nodes (\d+)")
FEN="rn3rk1/pp2bpp1/1q2pnbp/3p4/N2P1B1P/4P1N1/PP1Q1PP1/2R1KB1R b K - 11 16"

def conn():
    p=subprocess.Popen([BASE],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,bufsize=1)
    p.stdin.write("uci\n");p.stdin.flush(); opts=set()
    while True:
        l=p.stdout.readline()
        if not l: raise RuntimeError("died")
        s=l.strip()
        if s.startswith("option name "): opts.add(s.split("option name ")[1].split(" type ")[0])
        if s=="uciok": break
    if "OwnBook" in opts: p.stdin.write("setoption name OwnBook value false\n");p.stdin.flush()
    p.stdin.write("setoption name Threads value 1\nsetoption name Hash value 16\n");p.stdin.flush()
    p.stdin.write("isready\n");p.stdin.flush()
    while p.stdout.readline().strip()!="readyok": pass
    return p

def perft1():
    p=conn()
    p.stdin.write("ucinewgame\n");p.stdin.flush()
    p.stdin.write("position fen "+FEN+"\n");p.stdin.flush()
    p.stdin.write("isready\n");p.stdin.flush()
    while p.stdout.readline().strip()!="readyok": pass
    p.stdin.write("go perft 1\n");p.stdin.flush()
    order=[]; total=None
    while True:
        l=p.stdout.readline()
        if not l: raise RuntimeError("died in perft")
        s=l.strip()
        m=MOVELINE.match(s)
        if m: order.append((m.group(1),int(m.group(2))))
        ms=SUMMARY.match(s)
        if ms: total=int(ms.group(1)); break
    p.stdin.write("quit\n");p.stdin.flush()
    try: p.wait(timeout=10)
    except Exception: p.kill()
    return order,total

def search(depth=16):
    p=conn()
    p.stdin.write("ucinewgame\n");p.stdin.flush()
    p.stdin.write("position fen "+FEN+"\n");p.stdin.flush()
    p.stdin.write("isready\n");p.stdin.flush()
    while p.stdout.readline().strip()!="readyok": pass
    p.stdin.write("go depth %d\n"%depth);p.stdin.flush()
    last=None
    while True:
        l=p.stdout.readline()
        if not l: raise RuntimeError("died in search")
        s=l.strip(); m=INFO.match(s)
        if m: last=(m.group(2),int(m.group(3)),int(m.group(4)))
        if s.startswith("bestmove"):
            bm=s.split()[1]; break
    p.stdin.write("quit\n");p.stdin.flush()
    try: p.wait(timeout=10)
    except Exception: p.kill()
    return last,bm

order,total=perft1()
print("FEN:",FEN)
print("divide move lines parsed:",len(order),"| nodes total:",total)
if total is None or len(order)!=total:
    print("HARD FAILURE: parsed lines (%d) != nodes total (%s) - NOT A RESULT"%(len(order),total)); sys.exit(2)
moves=[m for m,_ in order]
print("first 6 generated:",moves[:6])
print("e6e5 index:", moves.index("e6e5") if "e6e5" in moves else "NOT IN DIVIDE")
print("e6e5 count:", dict(order).get("e6e5"))
print()
last,bm=search(16)
print("go depth 16 on the BARE fen:", ("%s %d"%last[:2]) if last else "no score", "| nodes", last[2] if last else "-", "| bestmove", bm)
