#!/usr/bin/env python3
"""partial_clock.py : 02-S-F4 — a `go` naming only the OPPONENT's clock searches unbounded, with no diagnostic.

Each probe sends a clock command and waits up to a budget for bestmove. Hangs are measured, not waited on.
CONTROLS: the matching clock MUST stop promptly, or the harness cannot tell "unbounded" from "slow".
"""
import subprocess, time, sys
PC="/home/ubuntu/pcbuild/forge"; BASE="/home/ubuntu/build/forge"
PC20=[l.strip() for l in open("../job7/pc20_opts.txt") if l.strip() and not l.startswith("#")]
OWB="setoption name OwnBook value false"
WHITE="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
BLACK="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR b KQkq - 0 1"
def probe(exe, opts, fen, cmd, budget=3.0):
    p=subprocess.Popen([exe],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,bufsize=1)
    p.stdin.write("uci\n");p.stdin.flush()
    names=set()
    while True:
        l=p.stdout.readline()
        if not l: return "died",0,0
        s=l.strip()
        if s.startswith("option name "): names.add(s.split("option name ")[1].split(" type ")[0])
        if s=="uciok": break
    for line in list(opts)+[OWB]:
        nm=line.split("name ")[1].split(" value ")[0]
        if nm not in names: continue
        p.stdin.write(line+"\n");p.stdin.flush()
        p.stdin.write("isready\n");p.stdin.flush()
        while p.stdout.readline().strip()!="readyok": pass
    p.stdin.write("ucinewgame\n");p.stdin.flush()
    p.stdin.write("position fen "+fen+"\n");p.stdin.flush()
    p.stdin.write("isready\n");p.stdin.flush()
    while p.stdout.readline().strip()!="readyok": pass
    t=time.monotonic(); p.stdin.write(cmd+"\n");p.stdin.flush()
    diag=0; bm=None
    while True:
        if time.monotonic()-t>budget:
            p.kill(); return "UNBOUNDED >%.0fs"%budget, diag, time.monotonic()-t
        try:
            l=p.stdout.readline()
        except: break
        if not l: break
        s=l.strip()
        if s.startswith("info string"): diag+=1
        if s.startswith("bestmove"): bm=s; break
    w=time.monotonic()-t
    p.stdin.write("quit\n");p.stdin.flush()
    try: p.wait(timeout=3)
    except: p.kill()
    return ("answered %.2fs"%w), diag, w
CASES=[
 ("Black to move, `go wtime 1000` (only White's clock)", BLACK, "go wtime 1000"),
 ("Black to move, `go btime 1000` (Black's own clock)",   BLACK, "go btime 1000"),
 ("White to move, `go btime 1000` (only Black's clock)",  WHITE, "go btime 1000"),
 ("White to move, `go wtime 1000` (White's own clock)",   WHITE, "go wtime 1000"),
]
for name,exe,opts in (("PC r15 + PC20",PC,PC20),("base",BASE,[])):
    print("==",name)
    print("| probe | outcome | info-string lines |")
    print("|---|---|---|")
    for label,fen,cmd in CASES:
        out,diag,w=probe(exe,opts,fen,cmd)
        print("| %s | %s | %d |"%(label,out,diag))
    print()
