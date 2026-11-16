#!/usr/bin/env python3
"""check_21f12.py -- does the PC build's drawn-root repair reach `searchmoves`?

Seat 21's 21-F12 says: at halfmove 100, `go searchmoves e1e8 depth 4` SEARCHES (8 nodes) on the PC
build where the base answers 0 nodes, while the "no legal named move" case is unchanged (0000,
0 nodes). If true it sharpens my 07-F1: the restriction path is fixed for a LEGAL named move at a
drawn root, but not for an empty one.

Measure on both builds, Threads 1, Hash 16, fresh process per cell, and read every line.
"""
import json, os, queue, re, subprocess, sys, threading

PC20_S14=["LmrQuietBase value 93","LmrQuietDivisor value 205","LmrNoisyBase value 13",
 "LmrNoisyDivisor value 333","LmrHistoryDivisor value 5643","NullMoveBase value 5","LmpBase value 8",
 "HistoryPruneMultiplier value 2220","HistoryBonusQuadratic value 24","HistoryBonusLinear value 54",
 "HistoryBonusMax value 2212","SingularDepth value 6","IirDepth value 2","NonPawnCorrection value true"]
PC20=PC20_S14+["CuckooRep value true","HistRework value 2","TtPruneV2 value true",
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
        l=r.get(60)
        if l is None or l.strip()=="uciok": break
    for o in ["Hash value 16","Threads value 1"]+opts:
        send("setoption name "+o); send("isready"); drain()
    send("ucinewgame"); send("isready"); drain()
    send("position fen "+fen); send("isready"); drain()
    send(go)
    lines=[];best=None;nodes=None;score=None
    while True:
        l=r.get(300)
        if l is None: break
        lines.append(l.rstrip())
        if l.startswith("info depth"):
            m=re.search(r" nodes (\d+) ",l+" ")
            if m: nodes=int(m.group(1))
            m=re.search(r"score (cp|mate) (-?\d+)",l)
            if m: score=f"{m.group(1)} {m.group(2)}"
        if l.startswith("bestmove"):
            best=l.split()[1]; break
    send("quit")
    try: p.wait(timeout=30)
    except subprocess.TimeoutExpired: p.kill()
    return {"best":best,"nodes":nodes,"score":score,
            "depth_lines":sum(1 for x in lines if x.startswith("info depth")),
            "info_strings":[x for x in lines if x.startswith("info string")]}

# My first attempt used `7k/6Q1/6K1/8/8/8/8/8 w - - 100 1`, which the ENGINE REFUSES with
# "side that moved left its king in check" (the black king is in check with White to move). The engine
# then kept STARTPOS and every answer was about the wrong position -- plain_at_hm100 answered e2e4,
# which was the tell. python-chess also rejects it as invalid-for-history.
#
# Valid substitutes, verified with python-chess first:
#   6k1/5Q2/6K1/8/8/8/8/8 b - - 100 1  -> 1 legal move for Black, so a named LEGAL move exists
#   7k/5Q2/6K1/8/8/8/8/8 b - - 100 1  -> 0 legal moves (stalemate), the no-legal-move case
FEN100="6k1/5Q2/6K1/8/8/8/8/8 b - - 100 1"          # Black to move, one legal move (g8h8), verified with python-chess
FEN100_NOMOVE="7k/5Q2/6K1/8/8/8/8/8 b - - 100 1"     # stalemate at counter 100
CASES=[
 ("legal_named_at_hm100", FEN100, "go searchmoves g8h8 depth 4"),
 ("no_legal_named_at_hm100", FEN100, "go searchmoves a1a2 depth 4"),
 ("plain_at_hm100", FEN100, "go depth 4"),
 ("stalemate_at_hm100", FEN100_NOMOVE, "go depth 4"),
]
def main():
    pc,base,outdir=sys.argv[1],sys.argv[2],sys.argv[3]
    os.makedirs(outdir,exist_ok=True)
    rows=[]
    for name,fen,go in CASES:
        b=run(base,fen,go,[])
        p=run(pc,fen,go,PC20)
        rows.append({"case":name,"base":b,"pc":p})
        print(f"{name}")
        print(f"   base: best {b['best']:>6} nodes {str(b['nodes']):>6} depthlines {b['depth_lines']:>2} {b['info_strings']}")
        print(f"   pc  : best {p['best']:>6} nodes {str(p['nodes']):>6} depthlines {p['depth_lines']:>2} {p['info_strings']}")
    json.dump(rows,open(os.path.join(outdir,"check_21f12.json"),"w"),indent=1)
if __name__=="__main__": main()
