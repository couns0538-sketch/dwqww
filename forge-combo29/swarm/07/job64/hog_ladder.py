#!/usr/bin/env python3
"""hog_ladder.py -- does CPU saturation change the MOVE, and where is the threshold?

Seat 30's 30-F64 / 30-C63: on a 4-core box, 0/1/2 busy processes leave the answer IDENTICAL to the
node (d2d3 d18 / 854,603), while 4 hogs (full saturation) flip the move to e1g1 at d15 / 205,048.

My check on MY OWN box: same design, same position, `go wtime 6000 btime 6000 winc 60 binc 60`, PC20,
Threads 1, two runs per cell, N hogs where N = 0, 1, 2, and nproc (full saturation). The hogs are
pure CPU burners (`yes > /dev/null`-style), killed afterwards.

Two purposes:
  1. reproduce the threshold (light load safe, full saturation not);
  2. establish whether MY OWN night's measurements are safe -- my box shows loadavg 0.1 and no forge
     processes, so if light load is provably harmless, my results stand.
"""
import json, os, queue, re, subprocess, sys, threading, time

S14=["LmrQuietBase value 93","LmrQuietDivisor value 205","LmrNoisyBase value 13",
 "LmrNoisyDivisor value 333","LmrHistoryDivisor value 5643","NullMoveBase value 5","LmpBase value 8",
 "HistoryPruneMultiplier value 2220","HistoryBonusQuadratic value 24","HistoryBonusLinear value 54",
 "HistoryBonusMax value 2212","SingularDepth value 6","IirDepth value 2","NonPawnCorrection value true"]
PC20=S14+["CuckooRep value true","HistRework value 2","TtPruneV2 value true",
 "CorrHistV2 value true","MateAlphaGuard value true","OwnBook value false"]
FEN="r1bq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N1PN2/PP3PPP/R2QKB1R w KQ - 0 8"

class R:
    def __init__(s,st):
        s.q=queue.Queue(); threading.Thread(target=s._pump,args=(st,),daemon=True).start()
    def _pump(s,st):
        for l in st: s.q.put(l)
        s.q.put(None)
    def get(s,t=15000):
        try: return s.q.get(timeout=t)
        except queue.Empty: return None

def run(exe):
    p=subprocess.Popen([exe],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True,bufsize=1)
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
    t0=time.monotonic(); send("go wtime 6000 btime 6000 winc 60 binc 60")
    depth=0;best=None;nodes=None
    while True:
        l=r.get(15000)
        if l is None: break
        if l.startswith("info depth"):
            m=re.match(r"info depth (\d+)",l)
            if m: depth=max(depth,int(m.group(1)))
            m=re.search(r" nodes (\d+) ",l+" ")
            if m: nodes=int(m.group(1))
        if l.startswith("bestmove"):
            best=l.split()[1]; break
    wall=(time.monotonic()-t0)*1000.0
    send("quit")
    try: p.wait(timeout=30)
    except subprocess.TimeoutExpired: p.kill()
    return {"best":best,"depth":depth,"nodes":nodes,"wall_ms":round(wall,1)}

def main():
    exe,outdir=sys.argv[1],sys.argv[2]
    cores=int(subprocess.run(["nproc"],capture_output=True,text=True).stdout.strip())
    os.makedirs(outdir,exist_ok=True)
    print(f"box has {cores} cores",flush=True)
    rows=[]
    for hogs in (0,1,2,cores):
        procs=[subprocess.Popen(["bash","-c","while :; do :; done"],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
               for _ in range(hogs)]
        try:
            time.sleep(1.0)
            a=run(exe); b=run(exe)
        finally:
            for q in procs:
                q.kill()
            for q in procs:
                try: q.wait(timeout=5)
                except Exception: pass
        rows.append({"hogs":hogs,"run1":a,"run2":b})
        print(f"  {hogs} hogs: run1 {a['best']} d{a['depth']} {a['nodes']} {a['wall_ms']}ms | "
              f"run2 {b['best']} d{b['depth']} {b['nodes']} {b['wall_ms']}ms",flush=True)
        time.sleep(1.5)
    json.dump({"cores":cores,"rows":rows},open(os.path.join(outdir,"hog_ladder.json"),"w"),indent=1)
    base=rows[0]["run1"]
    print()
    same=[r["hogs"] for r in rows if r["run1"]["best"]==base["best"] and r["run1"]["nodes"]==base["nodes"]]
    diff=[r["hogs"] for r in rows if not (r["run1"]["best"]==base["best"] and r["run1"]["nodes"]==base["nodes"])]
    print(f"identical to the 0-hog answer: {same}")
    print(f"changed                              : {diff}")

if __name__=="__main__": main()
