#!/usr/bin/env python3
"""check_19f59.py -- is seat 19's F58 "mirror defect" a DEPTH LIMIT, not a preference for dying fast?

Seat 19's 19-F59: on `6k1/8/5K2/8/6r1/8/8/8 w`, `go depth 16` and `depth 20` both give f6e7 (cp -490,
mated in 17), but `go depth 24` gives f6f5 with `mate -15` (the 29-ply longest defence). So the
"mirror defect" is a depth limit: below the depth where the longer losing line is visible the search
cannot distinguish the moves.

Check on the PC build under PC20, Threads 1, Hash 16, fresh process per depth. Depth is a discrete,
reproducible quantity (07-C47). Also record whether the engine reports a mate score at each depth, so
"could not see it" is distinguished from "saw it and chose wrong".
"""
import json, os, queue, re, subprocess, sys, threading

S14=["LmrQuietBase value 93","LmrQuietDivisor value 205","LmrNoisyBase value 13",
 "LmrNoisyDivisor value 333","LmrHistoryDivisor value 5643","NullMoveBase value 5","LmpBase value 8",
 "HistoryPruneMultiplier value 2220","HistoryBonusQuadratic value 24","HistoryBonusLinear value 54",
 "HistoryBonusMax value 2212","SingularDepth value 6","IirDepth value 2","NonPawnCorrection value true"]
PC20=S14+["CuckooRep value true","HistRework value 2","TtPruneV2 value true",
 "CorrHistV2 value true","MateAlphaGuard value true","OwnBook value false"]
FEN="6k1/8/5K2/8/6r1/8/8/8 w - - 0 1"

class R:
    def __init__(s,st):
        s.q=queue.Queue(); threading.Thread(target=s._pump,args=(st,),daemon=True).start()
    def _pump(s,st):
        for l in st: s.q.put(l)
        s.q.put(None)
    def get(s,t=1200):
        try: return s.q.get(timeout=t)
        except queue.Empty: return None

def run(exe,depth):
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
    send(f"go depth {depth}")
    best=None;score=None;pv=None
    while True:
        l=r.get(1200)
        if l is None: break
        if l.startswith("info depth"):
            m=re.search(r"score (cp|mate) (-?\d+)",l)
            if m: score=f"{m.group(1)} {m.group(2)}"
            if " pv " in l: pv=l.split(" pv ",1)[1].split()
        if l.startswith("bestmove"):
            best=l.split()[1]; break
    send("quit")
    try: p.wait(timeout=30)
    except subprocess.TimeoutExpired: p.kill()
    return {"depth":depth,"best":best,"score":score,"pv":pv}

def main():
    exe,outdir=sys.argv[1],sys.argv[2]
    os.makedirs(outdir,exist_ok=True)
    rows=[]
    print("6k1/8/5K2/8/6r1/8/8/8 w -- White to move, lost. Is the choice a depth limit?")
    for d in (12,16,20,22,24,26):
        r=run(exe,d)
        rows.append(r)
        print(f"  go depth {d:>2}: best {str(r['best']):>6}  score {str(r['score']):>12}  "
              f"pv {len(r['pv'] or [])} plies",flush=True)
    json.dump(rows,open(os.path.join(outdir,"check_19f59.json"),"w"),indent=1)
    b16=[r for r in rows if r["depth"]==16][0]
    b24=[r for r in rows if r["depth"]==24][0]
    print()
    print(f"depth 16 best={b16['best']} score={b16['score']}   depth 24 best={b24['best']} score={b24['score']}")
    changed = b16["best"]!=b24["best"]
    print(f"bestmove changed between depth 16 and 24: {changed}")
    if changed:
        print("=> seat 19's 19-F59 CONFIRMED: the move changes at greater depth, consistent with")
        print("   a DEPTH LIMIT rather than a preference for a faster death.")
    else:
        print("=> does NOT reproduce as stated.")

if __name__=="__main__": main()
