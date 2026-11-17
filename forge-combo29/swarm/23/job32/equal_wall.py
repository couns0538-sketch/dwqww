#!/usr/bin/env python3
"""equal_wall.py : which bare-king switch carries the depth-13 explosion? Measured at an EQUAL wall-time cut.

My first attempt let the budget check drift past the limit (the loop blocks on readline), so each variant was cut at a
different time and its node count was a partial. This version kills on an independent timer, so every variant gets
exactly CUT seconds of search and the node count at the cut is comparable.
"""
import re, subprocess, threading, time, sys
INFO=re.compile(r"^info depth (\d+) .*?nodes (\d+)")
FEN="8/8/5Q1K/8/k7/8/8/8 w - - 87 60"
CUT=float(sys.argv[1]) if len(sys.argv)>1 else 30.0
PC20=["setoption name CuckooRep value true","setoption name HistRework value 2",
      "setoption name TpPruneV2 value true"]
def run(exe, pc20=True):
    p=subprocess.Popen([exe],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,bufsize=1)
    p.stdin.write("uci\n");p.stdin.flush()
    names=set()
    while True:
        l=p.stdout.readline()
        if not l: raise RuntimeError("died")
        s=l.strip()
        if s.startswith("option name "): names.add(s.split("option name ")[1].split(" type ")[0])
        if s=="uciok": break
    opts=["setoption name OwnBook value false"]
    if pc20:
        opts+=["setoption name CuckooRep value true","setoption name HistRework value 2",
               "setoption name TtPruneV2 value true","setoption name CorrHistV2 value true",
               "setoption name MateAlphaGuard value true"]
    for line in opts:
        nm=line.split("name ")[1].split(" value ")[0]
        if nm in names:
            p.stdin.write(line+"\n");p.stdin.flush()
            p.stdin.write("isready\n");p.stdin.flush()
            while p.stdout.readline().strip()!="readyok": pass
    p.stdin.write("ucinewgame\n");p.stdin.flush()
    p.stdin.write("position fen "+FEN+"\n");p.stdin.flush()
    p.stdin.write("isready\n");p.stdin.flush()
    while p.stdout.readline().strip()!="readyok": pass
    state={"depth":0,"nodes":0,"bm":None}
    def reader():
        for line in p.stdout:
            s=line.strip()
            if s.startswith("info depth"):
                m=INFO.match(s)
                if m:
                    state["depth"]=int(m.group(1)); state["nodes"]=int(m.group(2))
            elif s.startswith("bestmove"):
                state["bm"]=s.split()[1]
                break
    t=threading.Thread(target=reader,daemon=True); t.start()
    t0=time.monotonic(); p.stdin.write("go depth 30\n");p.stdin.flush()   # depth 30 so the CUT is what stops it
    time.sleep(CUT)
    p.kill()
    return state["depth"], state["nodes"], state["bm"]
print("board:",FEN,"| `go depth 30` killed at an EQUAL %.0f s cut | Threads 1, Hash 16, OwnBook false, PC20 switches"%CUT)
print()
print("| variant | LMR_CAP | ONE_THREAD | depth at cut | nodes at cut |")
print("|---|---|---|---|---|")
for v,lmr,one in (("A","1","0 (default)"),("B","0","0"),("C","1","1"),("D","0","1")):
    d,n,bm=run("/home/ubuntu/variants/%s/forge"%v)
    print("| %s | %s | %s | %s | %s |"%(v,lmr,one,d if d else ("finished" if bm else "?"),n))
