#!/usr/bin/env python3
"""check_11sf91.py -- is FORGE_FIX_HARD_LIMIT_EMERGENCY's real benefit DETERMINISM?

Seat 11's S-F91: sweeping `go wtime t btime t` for t = 11..60 on PC20, 5 of 50 clock values differ
between the shipped build (switch ON) and a build with only that switch OFF, and at t = 17 the MOVE
differs. Repeating 5x with fresh processes: ON was stable (601 nodes 5/5), OFF was unstable.

My check: sweep the same grid on my own build pair (shipped ON vs only-this-switch OFF), then repeat
the differing clock values 5x each to test the determinism claim directly. Any value where the same
binary gives two different answers is instability.

PC r15 / PC20, Threads 1, Hash 16, fresh process per cell.
"""
import json, os, queue, subprocess, sys, threading

S14=["LmrQuietBase value 93","LmrQuietDivisor value 205","LmrNoisyBase value 13",
 "LmrNoisyDivisor value 333","LmrHistoryDivisor value 5643","NullMoveBase value 5","LmpBase value 8",
 "HistoryPruneMultiplier value 2220","HistoryBonusQuadratic value 24","HistoryBonusLinear value 54",
 "HistoryBonusMax value 2212","SingularDepth value 6","IirDepth value 2","NonPawnCorrection value true"]
PC20=S14+["CuckooRep value true","HistRework value 2","TtPruneV2 value true",
 "CorrHistV2 value true","MateAlphaGuard value true","OwnBook value false"]
FEN="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

class R:
    def __init__(s,st):
        s.q=queue.Queue(); threading.Thread(target=s._pump,args=(st,),daemon=True).start()
    def _pump(s,st):
        for l in st: s.q.put(l)
        s.q.put(None)
    def get(s,t=120):
        try: return s.q.get(timeout=t)
        except queue.Empty: return None

def run(exe,t):
    p=subprocess.Popen([exe],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,bufsize=1)
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
    for o in ["Hash value 16","Threads value 1"]+PC20:
        send("setoption name "+o); send("isready"); drain()
    send("ucinewgame"); send("isready"); drain()
    send("position fen "+FEN); send("isready"); drain()
    send(f"go wtime {t} btime {t}")
    best=None;nodes=None
    while True:
        l=r.get(120)
        if l is None: break
        if l.startswith("info depth"):
            parts=l.split()
            for i,x in enumerate(parts):
                if x=="nodes" and i+1<len(parts):
                    try: nodes=int(parts[i+1])
                    except ValueError: pass
        if l.startswith("bestmove"):
            best=l.split()[1]; break
    send("quit")
    try: p.wait(timeout=20)
    except subprocess.TimeoutExpired: p.kill()
    return best,nodes

def main():
    on,off,outdir=sys.argv[1],sys.argv[2],sys.argv[3]
    os.makedirs(outdir,exist_ok=True)
    diffs=[]
    print("sweep t = 11..60, ON vs OFF (switch only):")
    for t in range(11,61):
        a=run(on,t); b=run(off,t)
        if a!=b:
            diffs.append({"t":t,"on":a,"off":b})
            print(f"  t={t:>3}: ON {a}   OFF {b}   DIFFERS",flush=True)
    print(f"\ndiffering clock values: {len(diffs)} of 50 -> {[d['t'] for d in diffs]}")
    json.dump(diffs,open(os.path.join(outdir,"sweep.json"),"w"),indent=1)

    # determinism: repeat the differing values 5x each on both builds
    print("\ndeterminism, 5 fresh runs per cell on the differing values:")
    det={}
    for d in diffs:
        t=d["t"]
        onruns=[run(on,t) for _ in range(5)]
        offruns=[run(off,t) for _ in range(5)]
        on_stable=len(set(onruns))==1
        off_stable=len(set(offruns))==1
        det[t]={"on":onruns,"off":offruns,"on_stable":on_stable,"off_stable":off_stable}
        print(f"  t={t:>3}: ON stable={on_stable} {set(onruns)}   OFF stable={off_stable} {set(offruns)}",flush=True)
    json.dump(det,open(os.path.join(outdir,"determinism.json"),"w"),indent=1)
    n_off_unstable=sum(1 for v in det.values() if not v["off_stable"])
    n_on_unstable=sum(1 for v in det.values() if not v["on_stable"])
    print(f"\nsummary: OFF unstable at {n_off_unstable} of {len(det)} values; ON unstable at {n_on_unstable}")

if __name__=="__main__": main()
