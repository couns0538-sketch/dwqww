#!/usr/bin/env python3
"""check_08f30.py -- is the SPARSE endgame class also the volatile-score class?

Seat 08's 08-F30: on 5 boards per class at PC r15/PC20/Threads 1 with 6 s + 0.06, comparing the CLOCKED
stop to a COMPLETED `go depth D+4`:
  sparse: a MATE APPEARED on 2 of 5 boards (cp -4161 -> mate -5; cp 627 -> mate 12) and 318 cp median
          movement on the rest;
  full-material middlegames: 0 of 5 mates, 3 cp median movement.

They explicitly decline to quote a combined ratio because mapping mate to 30000 cp is meaningless --
which is the incomparable-units rule in my own header, so their handling is right.

My check: build my OWN sparse endgames (few pieces) and middlegames (full material), clock each at
6 s + 0.06, record the clocked score, then a COMPLETED `go depth D+4` on the same board, and compare.
Report per class: how many boards gained a mate, and the median |cp| movement among non-mate boards.
Mate-to-cp arithmetic is NOT performed (same reason they declined).
"""
import json, os, queue, re, subprocess, sys, threading, time
import chess

S14=["LmrQuietBase value 93","LmrQuietDivisor value 205","LmrNoisyBase value 13",
 "LmrNoisyDivisor value 333","LmrHistoryDivisor value 5643","NullMoveBase value 5","LmpBase value 8",
 "HistoryPruneMultiplier value 2220","HistoryBonusQuadratic value 24","HistoryBonusLinear value 54",
 "HistoryBonusMax value 2212","SingularDepth value 6","IirDepth value 2","NonPawnCorrection value true"]
PC20=S14+["CuckooRep value true","HistRework value 2","TtPruneV2 value true",
 "CorrHistV2 value true","MateAlphaGuard value true","OwnBook value false"]

# sparse endgames: few pieces, a queen or rook plus a passer against a king
SPARSE=[
 "8/8/8/4k3/8/8/4P3/R3K3 w - - 0 1",
 "8/8/8/5k2/8/8/4P3/3RK3 w - - 0 1",
 "8/8/4k3/8/8/8/4P3/3QK3 w - - 0 1",
 "8/8/8/3k4/8/8/3PP3/2R1K3 w - - 0 1",
 "8/8/5k2/8/8/8/4P3/2Q1K3 w - - 0 1",
]
# full-material middlegames
MID=[
 "r1bq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N1PN2/PP3PPP/R2QKB1R w KQ - 0 8",
 "r1bqkb1r/ppp2ppp/2np1n2/4p3/2B1P3/2NP1N2/PPP2PPP/R1BQK2R w KQkq - 0 6",
 "r2q1rk1/ppp2ppp/2n1bn2/2bpp3/3PP3/2N1BN2/PPP1BPPP/R2Q1RK1 w - - 0 9",
 "rnbq1rk1/pp3ppp/2pb1n2/3p4/2PP4/2N1PN2/PP2BPPP/R1BQK2R w KQ - 0 8",
 "r1bqk2r/pppp1ppp/2n2n2/2b1p3/2B1P3/2NP1N2/PPP2PPP/R1BQK2R w KQkq - 0 6",
]

class R:
    def __init__(s,st):
        s.q=queue.Queue(); threading.Thread(target=s._pump,args=(st,),daemon=True).start()
    def _pump(s,st):
        for l in st: s.q.put(l)
        s.q.put(None)
    def get(s,t=15000):
        try: return s.q.get(timeout=t)
        except queue.Empty: return None

def search(exe,fen,go):
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
    send("position fen "+fen); send("isready"); drain()
    send(go)
    score=None;depth=0;best=None
    while True:
        l=r.get(15000)
        if l is None: break
        if l.startswith("info depth"):
            m=re.match(r"info depth (\d+)",l)
            if m: depth=max(depth,int(m.group(1)))
            m=re.search(r"score (cp|mate) (-?\d+)",l)
            if m: score=(m.group(1),int(m.group(2)))
        if l.startswith("bestmove"):
            best=l.split()[1]; break
    send("quit")
    try: p.wait(timeout=30)
    except subprocess.TimeoutExpired: p.kill()
    return {"score":score,"depth":depth,"best":best}

def cp(sc):
    if sc is None: return None
    k,v=sc
    return v if k=="cp" else None   # mate scores are NOT converted (incomparable units)

def main():
    exe,outdir=sys.argv[1],sys.argv[2]
    os.makedirs(outdir,exist_ok=True)
    rows=[]
    for cls,boards in (("sparse",SPARSE),("middlegame",MID)):
        gains=0; moves=[]
        for fen in boards:
            c=search(exe,fen,"go wtime 6000 btime 6000 winc 60 binc 60")
            d=c["depth"]+4
            complete=search(exe,fen,f"go depth {d}")
            ck=c["score"][0] if c["score"] else None
            dk=complete["score"][0] if complete["score"] else None
            gained = (dk=="mate" and ck!="mate")
            if gained: gains+=1
            a,b=cp(c["score"]),cp(complete["score"])
            mv=abs(b-a) if (a is not None and b is not None) else None
            if mv is not None: moves.append(mv)
            rows.append({"class":cls,"fen":fen,"clocked":c,"complete_depth":d,
                         "complete":complete,"gained_mate":gained,"cp_move":mv})
            print(f"  {cls:11s} clocked d{c['depth']:>2} {str(c['score']):>12}  "
                  f"complete d{d:>2} {str(complete['score']):>12}  "
                  f"{'MATE APPEARED' if gained else ('cp move '+str(mv) if mv is not None else 'n/a')}",
                  flush=True)
    json.dump(rows,open(os.path.join(outdir,"check_08f30.json"),"w"),indent=1)
    print()
    for cls in ("sparse","middlegame"):
        rs=[r for r in rows if r["class"]==cls]
        g=sum(1 for r in rs if r["gained_mate"])
        mv=sorted(r["cp_move"] for r in rs if r["cp_move"] is not None)
        med=mv[len(mv)//2] if mv else None
        print(f"{cls:11s}: {g}/{len(rs)} gained a mate; median cp move among non-mate boards {med}")

if __name__=="__main__": main()
