#!/usr/bin/env python3
"""check_11SF53.py : independent check of seat 11's S-F53.

Claim: `position fen <X>` and `position startpos moves <path to X>` are SEARCH-IDENTICAL on PC r15 under PC20
(Threads 1), including node counts — so a GUI may use either form without changing the engine's answer.

Method: for each opening, send BOTH forms and compare bestmove AND the reported node count at `go softnodes 2000`.
PC r15 + PC20 + OwnBook false, fresh process per search, drained.
CONTROL: the two forms must differ on a NON-reversible opening, i.e. after a capture — otherwise the harness cannot
distinguish "identical" from "blind". I use an opening with captures and check that fen-form and moves-form still
agree (they should, being the same position) AND that a DIFFERENT opening gives a different answer.
"""
import re, subprocess, sys
import chess
INFO = re.compile(r"^info depth (\d+).*?nodes (\d+)")
PC="/home/ubuntu/pcbuild/forge"
OPTS=[l.strip() for l in open("../job7/pc20_opts.txt") if l.strip() and not l.startswith("#")]
OPTS.append("setoption name OwnBook value false")

OPENINGS=[
 ("London","d2d4 d7d5 b1f3 g8f6 e2e3 c7c5"),
 ("Ruy","e2e4 e7e5 g1f3 b8c6 f1b4 a7a6"),
 ("Sicilian","e2e4 c7c5 g1f3 d7d6 d2d4 c5d4"),
 ("QGD","d2d4 d7d5 c2c4 e7e6 b1c3 g8f6"),
 ("capture line","e2e4 d7d5 e4d5 d8d5 b1c3 d5a5"),
]
def run(position_cmd):
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
        p.stdin.write(line+"\n");p.stdin.flush()
        p.stdin.write("isready\n");p.stdin.flush()
        while p.stdout.readline().strip()!="readyok": pass
    p.stdin.write("ucinewgame\n");p.stdin.flush()
    p.stdin.write(position_cmd+"\n");p.stdin.flush()
    p.stdin.write("isready\n");p.stdin.flush()
    while p.stdout.readline().strip()!="readyok": pass
    p.stdin.write("go softnodes 2000\n");p.stdin.flush()
    nodes=0; bm=None
    while True:
        l=p.stdout.readline()
        if not l: raise RuntimeError("died in search")
        s=l.strip()
        m=INFO.match(s)
        if m: nodes=int(m.group(2))
        if s.startswith("bestmove"): bm=s.split()[1]; break
    p.stdin.write("quit\n");p.stdin.flush()
    try: p.wait(timeout=10)
    except: p.kill()
    return bm, nodes
print("| opening | fen form | moves form | same? |")
print("|---|---|---|---|")
same=0
for name,mv in OPENINGS:
    b=chess.Board()
    for m in mv.split(): b.push(chess.Move.from_uci(m))
    fen=b.fen()
    f_bm,f_n=run("position fen "+fen)
    m_bm,m_n=run("position startpos moves "+mv)
    ok = (f_bm,f_n)==(m_bm,m_n)
    same+=ok
    print("| %s | %s @ %d | %s @ %d | %s |"%(name,f_bm,f_n,m_bm,m_n,"YES" if ok else "NO"))
print()
print("identical: %d of %d"%(same,len(OPENINGS)))
# control: a DIFFERENT opening must give a different result, else the harness is blind
b2=chess.Board()
for m in "e2e4 e7e5".split(): b2.push(chess.Move.from_uci(m))
x_bm,x_n=run("position fen "+b2.fen())
print("CONTROL (different position must differ): e2e4 e7e5 gives %s @ %d; first opening gave %s"
      % (x_bm,x_n,run("position startpos moves d2d4 d7d5 b1f3 g8f6 e2e3 c7c5")[0]))
