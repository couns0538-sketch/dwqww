#!/usr/bin/env python3
"""tiebreak_4_5.py : the matched 3-vs-5-legal-move pair that closes the last half of seat 20's S-F27.

Their source note says search.cpp:817-862 has TWO tie rules: scalar `score > best_score` for fewer than 4 remaining
moves, and an AVX2 chunk-max + ctz for 4 or more. S-F27 tested only 3-move positions. This tests both widths on
positions where every move is drawn (insufficient material), so all scores tie at cp 0.

  3 moves: 8/8/8/8/8/8/8/K6k w - - 0 1                      (K v K)
  5 moves: 8/8/8/8/8/8/8/KN4k1 w - - 0 1                    (K+N v K, insufficient material)

For each: is the returned bestmove the FIRST legal move in the engine's own generation order? The engine's order is
not printed, so I use python-chess's order as a reference and ALSO probe each move alone (all tie, so scores cannot
order them) — the question is only whether the two widths behave the SAME WAY as each other.
"""
import re, subprocess, sys
import chess

EXE = sys.argv[1] if len(sys.argv) > 1 else "/home/ubuntu/build/forge"
INFO = re.compile(r"^info depth (\d+) .*?score (cp|mate) (-?\d+)")

def go(fen, depth):
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    p.stdin.write("uci\n"); p.stdin.flush()
    names=set()
    while True:
        l=p.stdout.readline()
        if not l: raise RuntimeError("died")
        s=l.strip()
        if s.startswith("option name "): names.add(s.split("option name ")[1].split(" type ")[0])
        if s=="uciok": break
    for line in ["setoption name OwnBook value false"]:
        if "OwnBook" in names:
            p.stdin.write(line+"\n"); p.stdin.flush()
            p.stdin.write("isready\n"); p.stdin.flush()
            while p.stdout.readline().strip()!="readyok": pass
    p.stdin.write("ucinewgame\n"); p.stdin.flush()
    p.stdin.write("position fen "+fen+"\n"); p.stdin.flush()
    p.stdin.write("isready\n"); p.stdin.flush()
    while p.stdout.readline().strip()!="readyok": pass
    p.stdin.write("go depth %d\n" % depth); p.stdin.flush()
    last=None; bm=None
    while True:
        l=p.stdout.readline()
        if not l: raise RuntimeError("died in search")
        s=l.strip()
        m=INFO.match(s)
        if m: last=(m.group(2),int(m.group(3)))
        if s.startswith("bestmove"): bm=s.split()[1]; break
    p.stdin.write("quit\n"); p.stdin.flush()
    try: p.wait(timeout=10)
    except: p.kill()
    return last, bm

CASES=[("3 moves (K v K)","8/8/8/8/8/8/8/K6k w - - 0 1"),
       ("5 moves (K+N v K)","8/8/8/8/8/8/8/KN4k1 w - - 0 1")]
print("| case | n moves | python-chess order | engine bestmove | depth | score | bestmove is 1st? | index |")
print("|---|---|---|---|---|---|---|---|")
for label,fen in CASES:
    b=chess.Board(fen); order=[m.uci() for m in b.legal_moves]
    for d in (1,2,3):
        sc,bm=go(fen,d)
        idx=order.index(bm) if bm in order else -1
        print("| %s | %d | %s | %s | %d | %s %d | %s | %d |" % (label,len(order),",".join(order),bm,d,sc[0],sc[1],
              "yes" if idx==0 else "NO", idx))
