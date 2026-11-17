#!/usr/bin/env python3
"""check_20sf53.py -- is the zero-node report ONE habit across paths?

Seat 20's S-F53: "any path that reports without searching emits one info-depth line per depth, capped
at 64 when no depth is given", and the three known zero-node paths (terminal root, empty restriction,
bare `go searchmoves`) share one cause.

Check on BOTH builds, Threads 1, Hash 16, fresh process per cell: count info-depth lines and total nodes
for each zero-node path, and check the 64 cap. If the same shape appears on all three paths on both
builds, one fix direction covers them -- which makes my 07-F1 a symptom of a shared habit rather than a
searchmoves quirk.
"""
import json, os, queue, re, subprocess, sys, threading

S14=["LmrQuietBase value 93","LmrQuietDivisor value 205","LmrNoisyBase value 13",
 "LmrNoisyDivisor value 333","LmrHistoryDivisor value 5643","NullMoveBase value 5","LmpBase value 8",
 "HistoryPruneMultiplier value 2220","HistoryBonusQuadratic value 24","HistoryBonusLinear value 54",
 "HistoryBonusMax value 2212","SingularDepth value 6","IirDepth value 2","NonPawnCorrection value true"]
PC20=S14+["CuckooRep value true","HistRework value 2","TtPruneV2 value true",
 "CorrHistV2 value true","MateAlphaGuard value true","OwnBook value false"]
START="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
MATE="7k/6Q1/6K1/8/8/8/8/8 b - - 0 1"
CASES=[
 ("terminal_depth2", MATE, "go depth 2"),
 ("terminal_nodes100", MATE, "go nodes 100"),
 ("empty_sm_depth2", START, "go depth 2 searchmoves"),
 ("empty_sm_nodepth", START, "go searchmoves"),
 ("empty_sm_nodes100", START, "go nodes 100 searchmoves"),
 ("illegal_sm_nodepth", START, "go searchmoves e2e5"),
]

class R:
    def __init__(s,st):
        s.q=queue.Queue(); threading.Thread(target=s._pump,args=(st,),daemon=True).start()
    def _pump(s,st):
        for l in st: s.q.put(l)
        s.q.put(None)
    def get(s,t=300):
        try: return s.q.get(timeout=t)
        except queue.Empty: return None

def run(exe,fen,go,opts):
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
    for o in ["Hash value 16","Threads value 1"]+opts:
        send("setoption name "+o); send("isready"); drain()
    send("ucinewgame"); send("isready"); drain()
    send("position fen "+fen); send("isready"); drain()
    send(go)
    dlines=0;best=None;lastnodes=None
    while True:
        l=r.get(300)
        if l is None: break
        if l.startswith("info depth"):
            dlines+=1
            m=re.search(r" nodes (\d+) ",l+" ")
            if m: lastnodes=int(m.group(1))
        if l.startswith("bestmove"):
            best=l.split()[1]; break
    send("quit")
    try: p.wait(timeout=30)
    except subprocess.TimeoutExpired: p.kill()
    return {"dlines":dlines,"nodes":lastnodes,"best":best}

def main():
    pc,base,outdir=sys.argv[1],sys.argv[2],sys.argv[3]
    os.makedirs(outdir,exist_ok=True)
    rows=[]
    print(f"{'case':24s} {'base dlines/nodes/best':>30} {'PC dlines/nodes/best':>30}")
    for name,fen,go in CASES:
        b=run(base,fen,go,[])
        p=run(pc,fen,go,PC20)
        rows.append({"case":name,"go":go,"base":b,"pc":p})
        print(f"{name:24s} {str(b['dlines'])+'/'+str(b['nodes'])+'/'+str(b['best']):>30} "
              f"{str(p['dlines'])+'/'+str(p['nodes'])+'/'+str(p['best']):>30}",flush=True)
    json.dump(rows,open(os.path.join(outdir,"check_20sf53.json"),"w"),indent=1)
    print()
    cap64=[r["case"] for r in rows if r["base"]["dlines"]==64 or r["pc"]["dlines"]==64]
    print(f"cases showing the 64-line cap: {cap64}")
    allzero=[r["case"] for r in rows if (r["base"]["nodes"]==0 and r["pc"]["nodes"]==0)]
    print(f"cases with 0 nodes on BOTH builds: {allzero}")

if __name__=="__main__": main()
