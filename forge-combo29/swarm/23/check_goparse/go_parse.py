#!/usr/bin/env python3
"""go_parse.py : test FORGE_FIX_GO_PARSE — file 5 says the PC build never takes a `go` keyword as the VALUE of the
keyword before it. That is a parsing bug about inputs like `go depth go` or `go nodes go`.

Method: feed malformed `go` lines and record whether the engine hangs, answers, or errors. A parse bug that eats
`go` as a value typically shows as a missing bestmove or a nonsense depth. Each probe is drained and bounded by a
timeout so a hang is measured rather than waited on.
"""
import re, subprocess, time, sys
INFO = re.compile(r"^info depth (\d+)")

PROBES = [
 ("go depth go", "go depth go"),
 ("go nodes go", "go nodes go"),
 ("go movetime go", "go movetime go"),
 ("go depth go nodes 1000", "go depth go nodes 1000"),
 ("go wtime go btime go", "go wtime go btime go"),
 ("control: go depth 3", "go depth 3"),
 ("control: go nodes 5000", "go nodes 5000"),
]
def probe(exe, cmd, budget=5.0):
    p=subprocess.Popen([exe],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,bufsize=1)
    p.stdin.write("uci\n");p.stdin.flush()
    names=set()
    while True:
        l=p.stdout.readline()
        if not l: raise RuntimeError("died")
        s=l.strip()
        if s.startswith("option name "): names.add(s.split("option name ")[1].split(" type ")[0])
        if s=="uciok": break
    if "OwnBook" in names:
        p.stdin.write("setoption name OwnBook value false\n");p.stdin.flush()
        p.stdin.write("isready\n");p.stdin.flush()
        while p.stdout.readline().strip()!="readyok": pass
    p.stdin.write("ucinewgame\n");p.stdin.flush()
    p.stdin.write("position fen 8/8/8/8/8/8/8/K6k w - - 0 1\n");p.stdin.flush()
    p.stdin.write("isready\n");p.stdin.flush()
    while p.stdout.readline().strip()!="readyok": pass
    t=time.monotonic(); p.stdin.write(cmd+"\n");p.stdin.flush()
    depths=0; bm=None
    p.kill_delay=None
    while True:
        if time.monotonic()-t > budget:
            p.kill(); return "HANG>%.0fs"%budget, depths, None
        l=p.stdout.readline()
        if not l: break
        s=l.strip()
        if INFO.match(s): depths+=1
        if s.startswith("bestmove"): bm=s.split()[1]; break
    w=time.monotonic()-t
    p.stdin.write("quit\n");p.stdin.flush()
    try: p.wait(timeout=3)
    except: p.kill()
    return "%.2fs"%w, depths, bm
print("| probe | base | PC r15 |")
print("|---|---|---|")
for label,cmd in PROBES:
    out=[]
    for exe in ("/home/ubuntu/build/forge","/home/ubuntu/pcbuild/forge"):
        w,d,bm=probe(exe,cmd)
        out.append("%s, %d info, %s"%(w,d,bm))
    print("| %s | %s | %s |"%(label,out[0],out[1]))
