#!/usr/bin/env python3
"""drawn_root.py : the drawn-root defect on base vs PC build (FABLE_TO_swarm_3 item: base searches 0 nodes and
plays its first legal move on a drawn root, e.g. third occurrence or halfmove >= 100; the PC repairs it).

Position: a WON K+R vs K board with the halfmove clock at 150 (draw by the 50-move rule) — the base is expected to
return 0 nodes and a move without searching, the PC to search it.
"""
import re, subprocess, sys
INFO = re.compile(r"^info depth (\d+) .*?score (cp|mate) (-?\d+).*?nodes (\d+)")

def go(exe, fen, depth=8):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    p.stdin.write("uci\n"); p.stdin.flush()
    names=set()
    while True:
        l=p.stdout.readline()
        if not l: raise RuntimeError("died")
        s=l.strip()
        if s.startswith("option name "): names.add(s.split("option name ")[1].split(" type ")[0])
        if s=="uciok": break
    if "OwnBook" in names:
        p.stdin.write("setoption name OwnBook value false\n"); p.stdin.flush()
        p.stdin.write("isready\n"); p.stdin.flush()
        while p.stdout.readline().strip()!="readyok": pass
    p.stdin.write("ucinewgame\n"); p.stdin.flush()
    p.stdin.write("position fen "+fen+"\n"); p.stdin.flush()
    p.stdin.write("isready\n"); p.stdin.flush()
    while p.stdout.readline().strip()!="readyok": pass
    p.stdin.write("go depth %d\n" % depth); p.stdin.flush()
    lines=0; last=None
    while True:
        l=p.stdout.readline()
        if not l: raise RuntimeError("died in search")
        s=l.strip()
        m=INFO.match(s)
        if m: lines+=1; last=(m.group(2),int(m.group(3)),int(m.group(4)))
        if s.startswith("bestmove"): bm=s.split()[1]; break
    p.stdin.write("quit\n"); p.stdin.flush()
    try: p.wait(timeout=10)
    except: p.kill()
    return lines, last, bm

CASES=[("won KRvK, halfmove 0 (legal)","1K6/8/8/3R4/8/8/8/k7 w - - 0 1"),
       ("won KRvK, halfmove 150 (drawn)","1K6/8/8/3R4/8/8/8/k7 w - - 150 1"),
       ("KQ v K, halfmove 150 (drawn)","8/5K2/7Q/4k3/8/8/8/8 w - - 150 1")]
print("| case | build | info lines | last score | last nodes | bestmove |")
print("|---|---|---|---|---|---|")
for label,fen in CASES:
    for name,exe in (("base","/home/ubuntu/build/forge"),("PC r15","/home/ubuntu/pcbuild/forge")):
        lines,last,bm = go(exe,fen)
        print("| %s | %s | %d | %s | %s | %s |" % (label,name,lines,
              ("%s %d"%last[:2]) if last else "-", last[2] if last else "-", bm))
