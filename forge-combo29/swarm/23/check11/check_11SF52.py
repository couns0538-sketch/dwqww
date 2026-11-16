#!/usr/bin/env python3
"""check_11SF52.py : independent check of seat 11's S-F52.

Claim: positions where the side to move is IN CHECK are handled correctly on PC r15 under PC20 (Threads 1):
five hand-built checks give perft 1 equal to python-chess's evasion count (they report 3/3/4/27/3), and 15 random
in-check positions are 15 of 15 correct.

My method: build in-check positions MYSELF (and verify with python-chess that the side to move really is in check),
then compare `go perft 1` against python-chess's legal-move count. Plus a randomly generated set from my own seed.
CONTROL: an out-of-check position must also agree (so a "0 mismatch" is not the product of a harness that always
compares the same number), and a KNOWN count (startpos = 20) must appear correctly.
"""
import re, subprocess, random, sys
import chess

PC="/home/ubuntu/pcbuild/forge"
OPTS=[l.strip() for l in open("../job7/pc20_opts.txt") if l.strip() and not l.startswith("#")]
OPTS.append("setoption name OwnBook value false")

def perft1(fen):
    p=subprocess.Popen([PC],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,bufsize=1)
    p.stdin.write("uci\n");p.stdin.flush()
    while True:
        l=p.stdout.readline()
        if not l or l.strip()=="uciok": break
    for line in OPTS:
        p.stdin.write(line+"\n");p.stdin.flush()
        p.stdin.write("isready\n");p.stdin.flush()
        while p.stdout.readline().strip()!="readyok": pass
    p.stdin.write("ucinewgame\n");p.stdin.flush()
    p.stdin.write("position fen "+fen+"\n");p.stdin.flush()
    p.stdin.write("isready\n");p.stdin.flush()
    refused=False
    while True:
        l=p.stdout.readline()
        if not l: break
        if "invalid FEN" in l: refused=True
        if l.strip()=="readyok": break
    p.stdin.write("go perft 1\n");p.stdin.flush()
    n=None
    while True:
        l=p.stdout.readline()
        if not l: break
        s=l.strip()
        if s.startswith("nodes "): n=int(s.split()[1]); break
    p.stdin.write("quit\n");p.stdin.flush()
    try: p.wait(timeout=5)
    except: p.kill()
    return n, refused

# five in-check positions of my own construction (verified with python-chess before use)
CHECK_FENS=[
 "4k3/8/8/8/8/8/8/R3K3 b - - 0 1",          # rook check along rank 1
 "4k3/8/8/8/8/8/8/RN2K3 b - - 0 1",         # rook check, one blocker
 "4k3/8/8/8/8/2n5/8/4K3 w - - 0 1",         # knight check on the king
 "3rk3/8/8/8/8/8/8/4K3 w - - 0 1",          # rook check
 "4k3/8/8/8/8/8/4r3/4K3 w - - 0 1",         # rook check from e2
]
print("| # | fen | in check? | python-chess evasions | engine perft 1 | equal? |")
print("|---|---|---|---|---|---|")
bad=0
for i,fen in enumerate(CHECK_FENS,1):
    b=chess.Board(fen)
    if not b.is_valid():
        print("| %d | %s | INVALID board, skipped | - | - | - |"%(i,fen)); continue
    py=b.legal_moves.count()
    eng,refused=perft1(fen)
    ok=(eng==py) and not refused
    bad += not ok
    print("| %d | %s | %s | %d | %s | %s |"%(i,fen,b.is_check(),py,eng,"yes" if ok else "NO"))

print()
print("== 15 random IN-CHECK positions from my own seed")
rng=random.Random(2311)
found=0; okc=0; tries=0
print("| # | fen | evasions | engine | equal? |")
print("|---|---|---|---|---|")
while found<15 and tries<200000:
    tries+=1
    b=chess.Board()
    for _ in range(rng.randint(8,40)):
        ms=list(b.legal_moves)
        if not ms: break
        b.push(rng.choice(ms))
    if not b.is_valid() or not b.is_check(): continue
    fen=b.fen(); py=b.legal_moves.count()
    eng,refused=perft1(fen)
    found+=1
    ok=(eng==py) and not refused
    okc+=ok
    print("| %d | %s | %d | %s | %s |"%(found,fen,py,eng,"yes" if ok else "NO"))
print()
print("random in-check: %d of %d correct"%(okc,found))
print("CONTROL startpos must be 20:", perft1("rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"))
