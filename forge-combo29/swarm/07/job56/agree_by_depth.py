#!/usr/bin/env python3
"""agree_by_depth.py -- are S14-vs-PC20 move disagreements shallow-horizon noise?

Check of 29-F45, which seat 29 flags as OPEN and unconfirmed by a second seat:
  "agreement is FLAT across depth -- 87.5 % at depth 8, 87.5 % at 10, 85.0 % at 12, 92.5 % at 14
   (40 real-game positions each, Threads 1, Hash 16, PC r15). If the differences were horizon
   artefacts they would shrink as depth grew; they do not."

My check: SAME question, DISJOINT positions (the last 40 of G, where seat 29 does not say which 40
theirs were), all four depths, PC r15 build under S14 and under PC20, Threads 1, Hash 16, fresh
process per cell. Agreement = same bestmove in both regimes at that depth.

Flatness is the claim, so what matters is the SHAPE across depth, not whether my percentage equals
theirs. A falling-then-flattening curve would be horizon noise; a flat curve is a regime difference.
"""
import json, os, queue, re, subprocess, sys, threading
import chess

S14=["LmrQuietBase value 93","LmrQuietDivisor value 205","LmrNoisyBase value 13",
 "LmrNoisyDivisor value 333","LmrHistoryDivisor value 5643","NullMoveBase value 5","LmpBase value 8",
 "HistoryPruneMultiplier value 2220","HistoryBonusQuadratic value 24","HistoryBonusLinear value 54",
 "HistoryBonusMax value 2212","SingularDepth value 6","IirDepth value 2","NonPawnCorrection value true"]
PC20=S14+["CuckooRep value true","HistRework value 2","TtPruneV2 value true",
 "CorrHistV2 value true","MateAlphaGuard value true","OwnBook value false"]
DEPTHS=(8,10,12,14)

class R:
    def __init__(s,st):
        s.q=queue.Queue(); threading.Thread(target=s._pump,args=(st,),daemon=True).start()
    def _pump(s,st):
        for l in st: s.q.put(l)
        s.q.put(None)
    def get(s,t=600):
        try: return s.q.get(timeout=t)
        except queue.Empty: return None

def run(exe,fen,depth,opts):
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
    for o in ["Hash value 16","Threads value 1","OwnBook value false"]+opts:
        send("setoption name "+o); send("isready"); drain()
    send("ucinewgame"); send("isready"); drain()
    send("position fen "+fen); send("isready"); drain()
    send(f"go depth {depth}")
    best=None
    while True:
        l=r.get(600)
        if l is None: break
        if l.startswith("bestmove"):
            best=l.split()[1]; break
    send("quit")
    try: p.wait(timeout=30)
    except subprocess.TimeoutExpired: p.kill()
    if best is None: raise SystemExit(f"FAIL no bestmove {fen} d{depth}")
    return best

def main():
    exe,outdir=sys.argv[1],sys.argv[2]
    n=int(sys.argv[3]) if len(sys.argv)>3 else 40
    os.makedirs(outdir,exist_ok=True)
    # setfile: /tmp/set_G.epd (mine) or /tmp/R_2911.fens (seat 29's own set)
    setfile=os.environ.get("SETFILE","/tmp/set_G.epd")
    fens=[]
    for line in open(setfile,encoding='utf-8'):
        p=line.split()
        if len(p)>=4:
            f=" ".join(p[:6]) if len(p)>=6 else " ".join(p[:4])+" 0 1"
            try: chess.Board(f)
            except ValueError: continue
            fens.append(f)
    sample=fens[-n:] if "G.epd" in setfile else fens[:n]
    print(f"set {setfile}: {len(fens)} positions; using {len(sample)}",flush=True)
    rows=[]
    for depth in DEPTHS:
        agree=0
        for i,fen in enumerate(sample):
            a=run(exe,fen,depth,S14)
            b=run(exe,fen,depth,PC20)
            if a==b: agree+=1
        pct=100.0*agree/len(sample)
        rows.append({"depth":depth,"agree":agree,"n":len(sample),"pct":round(pct,1)})
        print(f"  depth {depth:>2}: S14 vs PC20 agree on {agree}/{len(sample)} = {pct:.1f} %",flush=True)
    json.dump(rows,open(os.path.join(outdir,"agree_by_depth.json"),"w"),indent=1)
    print()
    pcts=[r["pct"] for r in rows]
    print(f"percentages across depth: {pcts}")
    print(f"spread: {max(pcts)-min(pcts):.1f} points")
    # a horizon artefact would trend upward with depth
    trend=pcts[-1]-pcts[0]
    print(f"trend depth {DEPTHS[0]} -> {DEPTHS[-1]}: {trend:+.1f} points")
    print("seat 29 reported 87.5 / 87.5 / 85.0 / 92.5 (mean ~88), flat.")
    if abs(trend) <= 10:
        print("=> FLAT within this sample too: no upward trend, so not shrinking with depth.")
    else:
        print("=> NOT flat here; the horizon-noise account would be back in play.")

if __name__=="__main__": main()
