#!/usr/bin/env python3
"""Compare depth-12 searches of startpos with NonPawnCorrection false vs true.

NonPawnCorrection is handled by a DIFFERENT branch of uci.cpp's setoption chain than the spin
options (uci.cpp:403-421, a bool* table chosen by name comparison), so the S14 sum alone does not
prove it takes effect. If the flag were silently ignored, both runs would be identical.
"""
import os, queue, re, subprocess, sys, threading

class R:
    def __init__(s, st):
        s.q=queue.Queue(); threading.Thread(target=s._pump,args=(st,),daemon=True).start()
    def _pump(s, st):
        for l in st: s.q.put(l)
        s.q.put(None)
    def get(s,t=120):
        try: return s.q.get(timeout=t)
        except queue.Empty: return None

def run(exe, value):
    p=subprocess.Popen([exe],stdin=subprocess.PIPE,stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE,text=True,bufsize=1)
    r=R(p.stdout)
    def send(c): p.stdin.write(c+"\n"); p.stdin.flush()
    def drain():
        while True:
            l=r.get()
            if l is None: raise RuntimeError("no readyok")
            if l.strip()=="readyok": return
    send("uci")
    while True:
        l=r.get(30)
        if l is None or l.strip()=="uciok": break
    for opt in ["Hash value 16","Threads value 1","NonPawnCorrection value "+value]:
        send("setoption name "+opt); send("isready"); drain()
    send("ucinewgame"); send("isready"); drain()
    send("position startpos"); send("isready"); drain()
    send("go depth 12")
    nodes=score=None
    while True:
        l=r.get(180)
        if l is None: raise RuntimeError("no bestmove")
        if l.startswith("info depth 12") and " nodes " in l:
            m=re.search(r" nodes (\d+) ",l)
            if m: nodes=int(m.group(1))
            m=re.search(r"score (cp|mate) (-?\d+)",l)
            if m: score=(m.group(1),int(m.group(2)))
        if l.startswith("bestmove"): break
    send("quit")
    try: p.wait(timeout=20)
    except subprocess.TimeoutExpired: p.kill()
    if nodes is None: raise SystemExit(f"FAIL no nodes for NonPawnCorrection={value}")
    return nodes, score

def main():
    exe, outdir = sys.argv[1], sys.argv[2]
    os.makedirs(outdir, exist_ok=True)
    off = run(exe, "false"); on = run(exe, "true")
    print(f"NonPawnCorrection false: nodes {off[0]} score {off[1]}")
    print(f"NonPawnCorrection true : nodes {on[0]} score {on[1]}")
    with open(os.path.join(outdir,"result.txt"),"w") as fh:
        fh.write(f"false {off[0]} {off[1]}\ntrue {on[0]} {on[1]}\n")
    if off == on:
        print("RESULT: the flag had NO effect on this search -> it may be ignored")
        sys.exit(1)
    print("RESULT: the flag measurably changes the search, so it takes effect")

if __name__=="__main__": main()
