#!/usr/bin/env python3
"""settle_nodes.py -- settle the 2.4x (really ~26x) node discrepancy between two seats.

Seat 30's 30-F66: on board `5k2/8/8/8/8/8/8/1K1Q4 w - - 80 1` with the SAME counters (`- 80 1`),
  seat 27 reports depth 14 at 599,407,784 nodes (never reaching 15 in ~62 s),
  seat 10 reports depth 14 at  23,174,968 and depth 15 at 250,077,687 (up to 120 s).
They conclude the difference is node ACCOUNTING or SAMPLING, not position.

My measurement: run the board myself, record EVERY `info depth` line's `nodes` field verbatim, and
report the LAST node count at each depth plus the FIRST. That distinguishes the two hypotheses:
  * if the last-per-depth counts match seat 10, seat 27's number is a sampling artefact;
  * if they match seat 27, seat 10's is;
  * if neither, the builds differ.
Both builds (base and PC r15 under PC20) are run, because the seats may not have used the same one.

NO time limit trickery: the run is given up to 300 s per depth and stopped if depth 16 is reached.
"""
import json, os, queue, re, subprocess, sys, threading, time

S14=["LmrQuietBase value 93","LmrQuietDivisor value 205","LmrNoisyBase value 13",
 "LmrNoisyDivisor value 333","LmrHistoryDivisor value 5643","NullMoveBase value 5","LmpBase value 8",
 "HistoryPruneMultiplier value 2220","HistoryBonusQuadratic value 24","HistoryBonusLinear value 54",
 "HistoryBonusMax value 2212","SingularDepth value 6","IirDepth value 2","NonPawnCorrection value true"]
PC20=S14+["CuckooRep value true","HistRework value 2","TtPruneV2 value true",
 "CorrHistV2 value true","MateAlphaGuard value true","OwnBook value false"]
FEN="5k2/8/8/8/8/8/8/1K1Q4 w - - 80 1"

class R:
    def __init__(s,st):
        s.q=queue.Queue(); threading.Thread(target=s._pump,args=(st,),daemon=True).start()
    def _pump(s,st):
        for l in st: s.q.put(l)
        s.q.put(None)
    def get(s,t=1.0):
        try: return s.q.get(timeout=t)
        except queue.Empty: return None

def run(exe,opts,max_depth=16,limit_s=300):
    p=subprocess.Popen([exe],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True,bufsize=1)
    r=R(p.stdout)
    def send(c): p.stdin.write(c+"\n"); p.stdin.flush()
    send("uci")
    t_end=time.monotonic()+30
    while True:
        l=r.get(30)
        if l is None or l.strip()=="uciok": break
    for o in ["Hash value 16","Threads value 1"]+opts:
        send("setoption name "+o); send("isready")
        while True:
            l=r.get(30)
            if l is None or l.strip()=="readyok": break
    send("ucinewgame"); send("isready")
    while True:
        l=r.get(30)
        if l is None or l.strip()=="readyok": break
    send("position fen "+FEN); send("isready")
    while True:
        l=r.get(30)
        if l is None or l.strip()=="readyok": break
    t0=time.monotonic()
    send(f"go depth {max_depth}")
    by_depth={}
    done=False
    while True:
        l=r.get(5.0)
        if l is None:
            if time.monotonic()-t0>limit_s: break
            continue
        if l.startswith("info depth"):
            m=re.match(r"info depth (\d+).*?\bnodes (\d+)",l)
            if m:
                d=int(m.group(1)); n=int(m.group(2))
                by_depth.setdefault(d,[]).append(n)
        if l.startswith("bestmove"):
            done=True; break
        if time.monotonic()-t0>limit_s: break
    send("stop")
    try: send("quit")
    except Exception: pass
    try: p.wait(timeout=20)
    except subprocess.TimeoutExpired: p.kill()
    return {"by_depth":{d:{"first":v[0],"last":v[-1],"lines":len(v)} for d,v in sorted(by_depth.items())},
            "completed":done,"elapsed_s":round(time.monotonic()-t0,1)}

def main():
    base,pc,outdir=sys.argv[1],sys.argv[2],sys.argv[3]
    os.makedirs(outdir,exist_ok=True)
    out={}
    for name,exe,opts in (("base",base,[]),("pc_r15_pc20",pc,PC20)):
        r=run(exe,opts)
        out[name]=r
        print(f"=== {name} (completed={r['completed']}, {r['elapsed_s']} s) ===")
        for d,v in r["by_depth"].items():
            print(f"   depth {d:>2}: first {v['first']:>12}  last {v['last']:>12}  ({v['lines']} lines)")
        print(flush=True)
    json.dump(out,open(os.path.join(outdir,"settle_nodes.json"),"w"),indent=1)
    print("seat 27 claims depth 14 = 599,407,784 and never depth 15 in ~62 s")
    print("seat 10 claims depth 14 =  23,174,968 and depth 15 = 250,077,687")

if __name__=="__main__": main()
