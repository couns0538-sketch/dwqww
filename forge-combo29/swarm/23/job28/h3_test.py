#!/usr/bin/env python3
"""h3_test.py : validate the protocol's rule for hazard 3 — send BOTH clocks, and never wait forever.

A naive driver sends `go wtime N` only; a compliant driver sends both clocks. Measure whether each gets bestmove,
with a bounded wait so a hang is observed rather than waited on.
CONTROL: the compliant driver must ANSWER, or the harness cannot tell "protocol works" from "nothing answers".
"""
import subprocess, time
PC="/home/ubuntu/pcbuild/forge"
OPTS=[l.strip() for l in open("../job7/pc20_opts.txt") if l.strip() and not l.startswith("#")]+["setoption name OwnBook value false"]
BLACK="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR b KQkq - 0 1"
def probe(go_cmd, budget=3.0):
    p=subprocess.Popen([PC],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,bufsize=1)
    p.stdin.write("uci\n");p.stdin.flush()
    names=set()
    while True:
        l=p.stdout.readline()
        if not l: return "died",0
        s=l.strip()
        if s.startswith("option name "): names.add(s.split("option name ")[1].split(" type ")[0])
        if s=="uciok": break
    for line in OPTS:
        p.stdin.write(line+"\n");p.stdin.flush()
        p.stdin.write("isready\n");p.stdin.flush()
        while p.stdout.readline().strip()!="readyok": pass
    p.stdin.write("ucinewgame\n");p.stdin.flush()
    p.stdin.write("position fen "+BLACK+"\n");p.stdin.flush()
    p.stdin.write("isready\n");p.stdin.flush()
    while p.stdout.readline().strip()!="readyok": pass
    t=time.monotonic(); p.stdin.write(go_cmd+"\n");p.stdin.flush()
    diag=0
    while True:
        if time.monotonic()-t>budget:
            p.kill(); return "NO BESTMOVE in %.0fs"%budget, diag
        l=p.stdout.readline()
        if not l: return "died mid-search", diag
        s=l.strip()
        if s.startswith("info string"): diag+=1
        if s.startswith("bestmove"):
            w=time.monotonic()-t
            p.stdin.write("quit\n");p.stdin.flush()
            try: p.wait(timeout=3)
            except: p.kill()
            return "answered %.2fs (%s)"%(w,s.split()[1]), diag
print("Black to move; the clock that matters is btime.")
print("| driver | `go` sent | outcome | diagnostics |")
print("|---|---|---|---|")
for label,cmd in (("NAIVE","go wtime 1000"),
                  ("COMPLIANT","go wtime 1000 btime 1000 winc 10 binc 10")):
    out,diag=probe(cmd)
    print("| %s | `%s` | %s | %d |"%(label,cmd,out,diag))
