#!/usr/bin/env python3
"""threefold.py : the drawn-root case that COULD matter — a threefold repetition reached by a real move list,
with a won material advantage, on base vs PC r15.

The position after d5d6 a1b1 d6d5 b1a1 d5d6 a1b1 d6d5 b1a1 has occurred three times, so a draw is claimable and
the match program (file 6) ends the game at the third occurrence. The engine should still SEARCH it — the defect
was answering with 0 nodes — and the PC is reported repaired.
"""
import re, subprocess, sys
import chess

INFO = re.compile(r"^info depth (\d+) .*?score (cp|mate) (-?\d+).*?nodes (\d+)")
MOVES = "d5d6 a1b1 d6d5 b1a1 d5d6 a1b1 d6d5 b1a1"
BASE = "1K6/8/8/3R4/8/8/8/k7 w - - 0 1"

def go(exe, depth=8):
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
    # send the position as a MOVE LIST so the engine's own repetition detection sees the history
    p.stdin.write("position fen %s moves %s\n" % (BASE, MOVES)); p.stdin.flush()
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

b = chess.Board(BASE)
for m in MOVES.split(): b.push(chess.Move.from_uci(m))
print("root position after the move list:", b.fen())
print("python-chess threefold claimable at root:", b.can_claim_threefold_repetition())
print()
print("| build | info lines | last score | last nodes | bestmove |")
print("|---|---|---|---|---|")
for name,exe in (("base","/home/ubuntu/build/forge"),("PC r15","/home/ubuntu/pcbuild/forge")):
    lines,last,bm = go(exe)
    print("| %s | %d | %s | %s | %s |" % (name,lines,("%s %d"%last[:2]) if last else "-",
          last[2] if last else "-", bm))
