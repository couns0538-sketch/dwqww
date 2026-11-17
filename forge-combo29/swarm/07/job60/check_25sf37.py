#!/usr/bin/env python3
"""check_25sf37.py -- a "minimum one" floor across UCI limit fields, with `nodes` the exception?

Seat 25's S-F37, measured on PC r15/PC20/Threads 1/Hash 16:
  * `go depth 0` behaves as depth 1 (searches one ply, does not decline);
  * `go movetime 0` reaches depth 5 (a floor, not zero time);
  * `go nodes 0` answers immediately at depth 0 with a DIFFERENT move (g1e2 vs the normal f1e2),
    the documented "explicit zero node budget is an immediate bounded answer".

Check each exactly, plus the control each needs:
  * `go depth 0` must NOT equal `go nodes 0`'s behaviour, else "depth 0 searches" is unproven;
  * `go movetime 0` vs `go movetime 1` -- if both are the same, 0 is clamped like 1;
  * `go nodes 0`'s move must differ from the normal search's move (that is the claim).
Every cell a fresh process, Threads 1, Hash 16, OwnBook false.
"""
import json, os, queue, re, subprocess, sys, threading, time

S14=["LmrQuietBase value 93","LmrQuietDivisor value 205","LmrNoisyBase value 13",
 "LmrNoisyDivisor value 333","LmrHistoryDivisor value 5643","NullMoveBase value 5","LmpBase value 8",
 "HistoryPruneMultiplier value 2220","HistoryBonusQuadratic value 24","HistoryBonusLinear value 54",
 "HistoryBonusMax value 2212","SingularDepth value 6","IirDepth value 2","NonPawnCorrection value true"]
PC20=S14+["CuckooRep value true","HistRework value 2","TtPruneV2 value true",
 "CorrHistV2 value true","MateAlphaGuard value true","OwnBook value false"]
FEN="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
CELLS=[("depth0","go depth 0"),("depth1","go depth 1"),
       ("movetime0","go movetime 0"),("movetime1","go movetime 1"),
       ("nodes0","go nodes 0"),("nodes1","go nodes 1"),
       ("normal","go depth 10")]

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
    for o in ["Hash value 16","Threads value 1","OwnBook value false"]+PC20:
        send("setoption name "+o); send("isready"); drain()
    send("ucinewgame"); send("isready"); drain()
    send("position fen "+FEN); send("isready"); drain()
    t0=time.monotonic(); send(go)
    depth=0;best=None;nodes=None
    while True:
        l=r.get(12000)
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
    try: p.wait(timeout=20)
    except subprocess.TimeoutExpired: p.kill()
    return {"depth":depth,"best":best,"nodes":nodes,"wall_ms":round(wall,1)}

def main():
    exe,outdir=sys.argv[1],sys.argv[2]
    os.makedirs(outdir,exist_ok=True)
    res={}
    print(f"{'cell':12s} {'go command':16s} {'depth':>5} {'best':>6} {'nodes':>7} {'wall':>8}")
    for name,go in CELLS:
        r=run(exe,go); res[name]=r
        print(f"{name:12s} {go:16s} {r['depth']:>5} {str(r['best']):>6} {str(r['nodes']):>7} {r['wall_ms']:>8.1f}",
              flush=True)
    json.dump(res,open(os.path.join(outdir,"check_25sf37.json"),"w"),indent=1)
    print()
    d0,d1=res["depth0"],res["depth1"]
    m0,m1=res["movetime0"],res["movetime1"]
    n0,norm=res["nodes0"],res["normal"]
    print("CLAIM CHECKS:")
    print(f"  1. `go depth 0` searches one ply:      depth={d0['depth']} (expect 1)  -> "
          f"{'CONFIRMED' if d0['depth']==1 else 'NOT CONFIRMED'}")
    print(f"     control: same answer as `go depth 1`? {d0['best']==d1['best']} "
          f"({d0['best']} vs {d1['best']})")
    print(f"  2. `go movetime 0` reaches a real depth: depth={m0['depth']} wall={m0['wall_ms']} ms; "
          f"movetime 1 -> depth={m1['depth']}  -> "
          f"{'CONFIRMED (floor)' if m0['depth']>=2 else 'NOT CONFIRMED'}")
    print(f"  3. `go nodes 0` answers at depth 0 with a DIFFERENT move: depth={n0['depth']} "
          f"best={n0['best']} vs normal {norm['best']}  -> "
          f"{'CONFIRMED' if (n0['depth']==0 and n0['best']!=norm['best']) else 'NOT CONFIRMED'}")

if __name__=="__main__": main()
