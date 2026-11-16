#!/usr/bin/env python3
"""midbudget.py -- do the two small budgets fail on the same positions because both are simply
"too small"? Add an intermediate budget and see whether its failures are a SUBSET of theirs.

07-C43 showed 59 of ~70 disagreements with nodes 250000 are shared between softnodes 20000 and
nodes 50000. If both are "too small", an intermediate budget (100000) should fail on FEWER positions
and those should be largely a subset of the shared ones. If instead they fail for different reasons,
100000 will fail on positions neither of them fails on.

PC r15 under PC20, Threads 1, Hash 16, fresh process per cell.
"""
import json, os, queue, re, subprocess, sys, threading
import chess

S14=["LmrQuietBase value 93","LmrQuietDivisor value 205","LmrNoisyBase value 13",
     "LmrNoisyDivisor value 333","LmrHistoryDivisor value 5643","NullMoveBase value 5",
     "LmpBase value 8","HistoryPruneMultiplier value 2220","HistoryBonusQuadratic value 24",
     "HistoryBonusLinear value 54","HistoryBonusMax value 2212","SingularDepth value 6",
     "IirDepth value 2","NonPawnCorrection value true"]
PC20=S14+["CuckooRep value true","HistRework value 2","TtPruneV2 value true",
          "CorrHistV2 value true","MateAlphaGuard value true","OwnBook value false"]
BUDGETS=[("n20","go softnodes 20000"),("n50","go nodes 50000"),
         ("n100","go nodes 100000"),("n250","go nodes 250000")]

class R:
    def __init__(s,st):
        s.q=queue.Queue(); threading.Thread(target=s._pump,args=(st,),daemon=True).start()
    def _pump(s,st):
        for l in st: s.q.put(l)
        s.q.put(None)
    def get(s,t=900):
        try: return s.q.get(timeout=t)
        except queue.Empty: return None

def run(exe,fen,go):
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
        l=r.get(60)
        if l is None or l.strip()=="uciok": break
    for o in ["Hash value 16","Threads value 1"]+PC20:
        send("setoption name "+o); send("isready"); drain()
    send("ucinewgame"); send("isready"); drain()
    send("position fen "+fen); send("isready"); drain()
    send(go)
    best=None
    while True:
        l=r.get(900)
        if l is None: break
        if l.startswith("bestmove"):
            best=l.split()[1]; break
    send("quit")
    try: p.wait(timeout=60)
    except subprocess.TimeoutExpired: p.kill()
    if best is None: raise SystemExit(f"FAIL no bestmove for {go}")
    return best

def main():
    exe,outdir=sys.argv[1],sys.argv[2]
    limit=int(sys.argv[3]) if len(sys.argv)>3 else 120
    os.makedirs(outdir,exist_ok=True)
    fens=[]
    for line in open("/tmp/set_G.epd",encoding="utf-8"):
        p=line.split()
        if len(p)>=4:
            f=" ".join(p[:6]) if len(p)>=6 else " ".join(p[:4])+" 0 1"
            try: chess.Board(f)
            except ValueError: continue
            fens.append(f)
    sample=fens[:limit]
    print(f"{len(sample)} positions, budgets {[b[0] for b in BUDGETS]}",flush=True)
    rows=[]
    for i,fen in enumerate(sample):
        d={}
        for name,go in BUDGETS:
            d[name]=run(exe,fen,go)
        rows.append({"i":i,"fen":fen,**d})
        if (i+1)%30==0: print(f"  ...{i+1}/{len(sample)}",flush=True)
    json.dump(rows,open(os.path.join(outdir,"midbudget.json"),"w"),indent=1)

    def fails(name):
        return {r["i"] for r in rows if r[name]!=r["n250"]}
    f20,f50,f100=fails("n20"),fails("n50"),fails("n100")
    print()
    print(f"disagreements with n250: n20 {len(f20)}, n50 {len(f50)}, n100 {len(f100)}")
    print(f"  n100 failures that are also n20 failures: {len(f100&f20)}")
    print(f"  n100 failures that are also n50 failures: {len(f100&f50)}")
    print(f"  n100 failures on positions NEITHER small budget fails: {len(f100-f20-f50)}")
    print(f"  n20 failures that n100 fixes: {len(f20-f100)}")
    print()
    if len(f100) < len(f20) and len(f100-f20-f50)==0:
        print("RESULT: the intermediate budget's failures are a SUBSET of the small budgets' ->")
        print("        both small budgets are simply too small.")
    else:
        print("RESULT: the intermediate budget fails on positions the small budgets do not ->")
        print("        the budgets fail for different reasons, not just depth.")

if __name__=="__main__": main()
