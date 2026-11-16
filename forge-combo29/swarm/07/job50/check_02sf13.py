#!/usr/bin/env python3
"""check_02sf13.py -- is the owner's 6s+0.06 clock barely used?

Seat 02's S-F13/S-C6: on startpos, `go wtime 6000 btime 6000 winc 60 binc 60` gives 362 ms / depth 19,
IDENTICAL to `go depth 19` (360 ms, same nodes), while `go movetime 6000` gives 5990 ms / depth 27.
So the 6 s budget is usable and the clock path does not use it.

Measured here on the PC build under PC20, Threads 1, Hash 16, fresh process per cell, WALL CLOCK timed,
TWO runs per cell (07-C47 discipline: under a clock compare the MOVE and WALL TIME, not the node count).
Control: `go movetime 6000` must run near 6000 ms and reach a greater depth, else the harness cannot
see a long search.
"""
import json, os, queue, re, subprocess, sys, threading, time

S14=["LmrQuietBase value 93","LmrQuietDivisor value 205","LmrNoisyBase value 13",
 "LmrNoisyDivisor value 333","LmrHistoryDivisor value 5643","NullMoveBase value 5","LmpBase value 8",
 "HistoryPruneMultiplier value 2220","HistoryBonusQuadratic value 24","HistoryBonusLinear value 54",
 "HistoryBonusMax value 2212","SingularDepth value 6","IirDepth value 2","NonPawnCorrection value true"]
PC20=S14+["CuckooRep value true","HistRework value 2","TtPruneV2 value true",
 "CorrHistV2 value true","MateAlphaGuard value true","OwnBook value false"]
FEN="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
CELLS=[("clock_6s_0.06","go wtime 6000 btime 6000 winc 60 binc 60"),
       ("depth19","go depth 19"),
       ("movetime6000","go movetime 6000")]

class R:
    def __init__(s,st):
        s.q=queue.Queue(); threading.Thread(target=s._pump,args=(st,),daemon=True).start()
    def _pump(s,st):
        for l in st: s.q.put(l)
        s.q.put(None)
    def get(s,t=12000):
        try: return s.q.get(timeout=t)
        except queue.Empty: return None

def run(exe,go):
    p=subprocess.Popen([exe],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,bufsize=1)
    r=R(p.stdout)
    def send(c): p.stdin.write(c+"\n"); p.stdin.flush()
    def drain():
        while True:
            l=r.get(30)
            if l is None: raise RuntimeError("no readyok")
            if l.strip()=="readyok": return
    send("uci")
    while True:
        l=r.get(30)
        if l is None or l.strip()=="uciok": break
    for o in ["Hash value 16","Threads value 1"]+PC20:
        send("setoption name "+o); send("isready"); drain()
    send("ucinewgame"); send("isready"); drain()
    send("position fen "+FEN); send("isready"); drain()
    t0=time.monotonic(); send(go)
    maxdepth=0;best=None;nodes=None
    while True:
        l=r.get(12000)
        if l is None: break
        if l.startswith("info depth"):
            m=re.match(r"info depth (\d+)",l)
            if m: maxdepth=max(maxdepth,int(m.group(1)))
            m=re.search(r" nodes (\d+) ",l+" ")
            if m: nodes=int(m.group(1))
        if l.startswith("bestmove"):
            best=l.split()[1]; break
    wall=(time.monotonic()-t0)*1000.0
    send("quit")
    try: p.wait(timeout=30)
    except subprocess.TimeoutExpired: p.kill()
    return {"wall_ms":round(wall,1),"depth":maxdepth,"best":best,"nodes":nodes}

def main():
    exe,outdir=sys.argv[1],sys.argv[2]
    os.makedirs(outdir,exist_ok=True)
    rows=[]
    print(f"{'cell':16s} {'run1 wall/depth/best':>34} {'run2 wall/depth/best':>34}")
    for name,go in CELLS:
        a=run(exe,go); b=run(exe,go)
        rows.append({"cell":name,"go":go,"run1":a,"run2":b})
        print(f"{name:16s} {str(a['wall_ms'])+'/'+str(a['depth'])+'/'+str(a['best']):>34} "
              f"{str(b['wall_ms'])+'/'+str(b['depth'])+'/'+str(b['best']):>34}",flush=True)
    json.dump(rows,open(os.path.join(outdir,"check_02sf13.json"),"w"),indent=1)
    print()
    clk=[r for r in rows if r["cell"]=="clock_6s_0.06"][0]["run1"]
    mv=[r for r in rows if r["cell"]=="movetime6000"][0]["run1"]
    d19=[r for r in rows if r["cell"]=="depth19"][0]["run1"]
    print(f"6 s clock uses {100.0*clk['wall_ms']/6000:.1f} % of the budget ({clk['wall_ms']} ms of 6000)")
    print(f"movetime 6000 uses {100.0*mv['wall_ms']/6000:.1f} % ({mv['wall_ms']} ms), depth {mv['depth']} vs clock depth {clk['depth']}")
    print(f"clock vs depth19: wall {clk['wall_ms']} vs {d19['wall_ms']}, best {clk['best']} vs {d19['best']}, "
          f"depth {clk['depth']} vs {d19['depth']}")
    if mv["wall_ms"] < 5000:
        print("CONTROL FAILED: movetime 6000 did not run near 6000 ms; no utilisation claim can be made")
    else:
        print("control passed: movetime 6000 runs the budget out, so the harness sees a long search")

if __name__=="__main__": main()
