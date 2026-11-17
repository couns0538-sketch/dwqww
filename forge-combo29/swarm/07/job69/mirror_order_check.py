#!/usr/bin/env python3
"""mirror_order_check.py -- is the colour-mirror asymmetry entirely MOVE-GENERATION ORDER?

Seat 16's S-F35 / S-F37: canonicalising all five generation sites by a mirror-invariant key makes
mirror node counts EXACTLY equal — 120 of 120 cases at depths 1-2 vs 34 of 120 on the base PC r15 build.

I have their patch (80 lines, applies with patch -p2 --fuzz=0) and built it. So this is a direct
replication, not a baseline estimate:
  ARM A: stock PC r15 under PC20   -> expect ~34/120 equal
  ARM B: their canonicalised build -> expect 120/120 equal
Same 60 G positions, depths 1 and 2, Threads 1, Hash 16, comparing mirrored pairs on NODE COUNTS
(07-C41's lesson: the invariant for a side-to-move-relative score under Board.mirror() is EQUALITY).

Control: the two arms must DIFFER on the base arm, or the test cannot see an asymmetry at all.
"""
import json, os, queue, re, subprocess, sys, threading
import chess

S14=["LmrQuietBase value 93","LmrQuietDivisor value 205","LmrNoisyBase value 13",
 "LmrNoisyDivisor value 333","LmrHistoryDivisor value 5643","NullMoveBase value 5","LmpBase value 8",
 "HistoryPruneMultiplier value 2220","HistoryBonusQuadratic value 24","HistoryBonusLinear value 54",
 "HistoryBonusMax value 2212","SingularDepth value 6","IirDepth value 2","NonPawnCorrection value true"]
PC20=S14+["CuckooRep value true","HistRework value 2","TtPruneV2 value true",
 "CorrHistV2 value true","MateAlphaGuard value true","OwnBook value false"]

class R:
    def __init__(s,st):
        s.q=queue.Queue(); threading.Thread(target=s._pump,args=(st,),daemon=True).start()
    def _pump(s,st):
        for l in st: s.q.put(l)
        s.q.put(None)
    def get(s,t=300):
        try: return s.q.get(timeout=t)
        except queue.Empty: return None

def nodes(exe,fen,depth):
    p=subprocess.Popen([exe],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True,bufsize=1)
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
    for o in ["Hash value 16","Threads value 1","OwnBook value false"]+PC20:
        send("setoption name "+o); send("isready"); drain()
    send("ucinewgame"); send("isready"); drain()
    send("position fen "+fen); send("isready"); drain()
    send(f"go depth {depth}")
    n=None
    while True:
        l=r.get(300)
        if l is None: break
        if l.startswith("depth"): pass
        m=re.search(r"^\S*\s*nodes (\d+)",l) if False else None
        if l.startswith("info depth"):
            m=re.search(r" nodes (\d+) ",l+" ")
            if m: n=int(m.group(1))
        if l.startswith("bestmove"): break
    send("quit")
    try: p.wait(timeout=20)
    except subprocess.TimeoutExpired: p.kill()
    return n

def main():
    stock,canon,outdir=sys.argv[1],sys.argv[2],sys.argv[3]
    n=int(sys.argv[4]) if len(sys.argv)>4 else 60
    os.makedirs(outdir,exist_ok=True)
    fens=[]
    for line in open('/tmp/set_G.epd',encoding='utf-8'):
        p=line.split()
        if len(p)>=4:
            f=" ".join(p[:6]) if len(p)>=6 else " ".join(p[:4])+" 0 1"
            try: chess.Board(f)
            except ValueError: continue
            fens.append(f)
    sample=fens[:n]
    res={"stock":{"equal":0,"cases":0},"canon":{"equal":0,"cases":0}}
    diffs=[]
    for i,fen in enumerate(sample):
        mir=chess.Board(fen).mirror().fen()
        for d in (1,2):
            a1=nodes(stock,fen,d); a2=nodes(stock,mir,d)
            b1=nodes(canon,fen,d); b2=nodes(canon,mir,d)
            res["stock"]["cases"]+=1; res["canon"]["cases"]+=1
            se=(a1==a2); ce=(b1==b2)
            if se: res["stock"]["equal"]+=1
            if ce: res["canon"]["equal"]+=1
            if not ce:
                diffs.append({"i":i,"depth":d,"stock":(a1,a2),"canon":(b1,b2),"fen":fen})
        if (i+1)%15==0:
            print(f"  ...{i+1}/{len(sample)}  stock {res['stock']['equal']}/{res['stock']['cases']}  "
                  f"canon {res['canon']['equal']}/{res['canon']['cases']}",flush=True)
    json.dump({"res":res,"diffs":diffs},open(os.path.join(outdir,"mirror_order_check.json"),"w"),indent=1)
    print()
    print(f"STOCK PC r15/PC20 : {res['stock']['equal']}/{res['stock']['cases']} mirror pairs equal")
    print(f"CANONICALISED     : {res['canon']['equal']}/{res['canon']['cases']} mirror pairs equal")
    print("seat 16 reports: base 34/120, canonicalised 120/120")
    if res["canon"]["equal"]<res["canon"]["cases"]:
        print(f"  residue in the canonicalised arm: {len(diffs)} cases")
        for x in diffs[:4]: print("   ", x)

if __name__=="__main__": main()
