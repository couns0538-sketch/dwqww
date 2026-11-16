#!/usr/bin/env python3
"""check_01sf72.py -- does MultiPV > 1 silently shrink a fixed node budget?

Seat 01's S-F72: with MultiPV>1 a fixed node budget buys far fewer plies (d10->d7 at 20,000 nodes;
d8->d2 on softnodes 2000), because the M lines are produced from the same N nodes.

Check on the PC build under PC20, Threads 1, Hash 16: for MultiPV in {1,2,3,4} measure the depth
reached at `go nodes 20000` and at `go softnodes 2000`, on TWO positions (startpos and a middlegame),
fresh process per cell, TWO runs per cell. Depth is a discrete reproducible quantity (07-C47); nodes
under a clock are not, so the comparison is on depth and bestmove, and node budget is a NODE stop
(not a clock), so node totals should be stable here too -- which the second run tests.

Controls: MultiPV 1 must reach a clearly greater depth than MultiPV 4 at a fixed budget, else the
harness cannot see dilution at all.
"""
import json, os, queue, re, subprocess, sys, threading

S14=["LmrQuietBase value 93","LmrQuietDivisor value 205","LmrNoisyBase value 13",
 "LmrNoisyDivisor value 333","LmrHistoryDivisor value 5643","NullMoveBase value 5","LmpBase value 8",
 "HistoryPruneMultiplier value 2220","HistoryBonusQuadratic value 24","HistoryBonusLinear value 54",
 "HistoryBonusMax value 2212","SingularDepth value 6","IirDepth value 2","NonPawnCorrection value true"]
PC20=S14+["CuckooRep value true","HistRework value 2","TtPruneV2 value true",
 "CorrHistV2 value true","MateAlphaGuard value true","OwnBook value false"]

POSITIONS={
 "startpos":"rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
 "middlegame":"r1bq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N1PN2/PP3PPP/R2QKB1R w KQ - 0 8",
}
BUDGETS=[("nodes20000","go nodes 20000"),("softnodes2000","go softnodes 2000")]

class R:
    def __init__(s,st):
        s.q=queue.Queue(); threading.Thread(target=s._pump,args=(st,),daemon=True).start()
    def _pump(s,st):
        for l in st: s.q.put(l)
        s.q.put(None)
    def get(s,t=300):
        try: return s.q.get(timeout=t)
        except queue.Empty: return None

def run(exe,fen,go,multipv):
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
    for o in ["Hash value 16","Threads value 1",f"MultiPV value {multipv}"]+PC20:
        send("setoption name "+o); send("isready"); drain()
    send("ucinewgame"); send("isready"); drain()
    send("position fen "+fen); send("isready"); drain()
    send(go)
    maxdepth=0; final_nodes=None; best=None
    while True:
        l=r.get(300)
        if l is None: break
        if l.startswith("info depth"):
            m=re.match(r"info depth (\d+)",l)
            if m: maxdepth=max(maxdepth,int(m.group(1)))
            m=re.search(r" nodes (\d+) ",l+" ")
            if m: final_nodes=int(m.group(1))
        if l.startswith("bestmove"):
            best=l.split()[1]; break
    send("quit")
    try: p.wait(timeout=30)
    except subprocess.TimeoutExpired: p.kill()
    return {"depth":maxdepth,"nodes":final_nodes,"best":best}

def main():
    exe,outdir=sys.argv[1],sys.argv[2]
    os.makedirs(outdir,exist_ok=True)
    rows=[]
    print(f"{'position':12s} {'budget':14s} {'mpv':>4} {'run1 d/n':>18} {'run2 d/n':>18} stable")
    for pname,fen in POSITIONS.items():
        for bname,go in BUDGETS:
            for mpv in (1,2,3,4):
                a=run(exe,fen,go,mpv); b=run(exe,fen,go,mpv)
                stable=(a["depth"]==b["depth"] and a["nodes"]==b["nodes"])
                rows.append({"pos":pname,"budget":bname,"multipv":mpv,"run1":a,"run2":b,"stable":stable})
                print(f"{pname:12s} {bname:14s} {mpv:>4} "
                      f"{str(a['depth'])+'/'+str(a['nodes']):>18} "
                      f"{str(b['depth'])+'/'+str(b['nodes']):>18} {stable}",flush=True)
    json.dump(rows,open(os.path.join(outdir,"check_01sf72.json"),"w"),indent=1)

    print()
    for pname in POSITIONS:
        for bname,_ in BUDGETS:
            d1=[r for r in rows if r["pos"]==pname and r["budget"]==bname and r["multipv"]==1][0]["run1"]["depth"]
            d4=[r for r in rows if r["pos"]==pname and r["budget"]==bname and r["multipv"]==4][0]["run1"]["depth"]
            print(f"  {pname:12s} {bname:14s} depth MPV1={d1} MPV4={d4} -> dilution {d1-d4} plies")

if __name__=="__main__": main()
