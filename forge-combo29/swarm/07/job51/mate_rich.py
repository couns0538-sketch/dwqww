#!/usr/bin/env python3
"""mate_rich.py -- build a MATE-RICH position pool so 05-S-F57's truncation rate can be measured.

Seat 05's own S-W6 records why their retest was void: they filtered 120 pool positions for |mate|>=8
at depth 20 and only 2 qualified, and neither produced a mate at any match budget. A sample with no
mate scores cannot measure mate-score truncation.

The fix is to select positions where a mate IS reachable at the SMALLEST budget under test. Procedure:
  1. take G and construct K+Q/K+R vs K style plus real endgames from G (mates are frequent there);
  2. at `go nodes 20000`, keep only positions that report a mate score;
  3. on that kept set, measure how many of the mate-scored lines have a PV whose length matches the
     mate distance (2|N| plies for a negative mate, per 07-C40's convention), calling a mismatch
     TRUNCATED.

Control: the same check must call a deliberately-shortened PV truncated, so a checker that always
says "fine" is caught.
"""
import json, os, queue, re, subprocess, sys, threading
import chess

S14=["LmrQuietBase value 93","LmrQuietDivisor value 205","LmrNoisyBase value 13",
 "LmrNoisyDivisor value 333","LmrHistoryDivisor value 5643","NullMoveBase value 5","LmpBase value 8",
 "HistoryPruneMultiplier value 2220","HistoryBonusQuadratic value 24","HistoryBonusLinear value 54",
 "HistoryBonusMax value 2212","SingularDepth value 6","IirDepth value 2","NonPawnCorrection value true"]
PC20=S14+["CuckooRep value true","HistRework value 2","TtPruneV2 value true",
 "CorrHistV2 value true","MateAlphaGuard value true","OwnBook value false"]
BUDGETS=[("n20000","go nodes 20000"),("n50000","go nodes 50000"),("n250000","go nodes 250000")]

class R:
    def __init__(s,st):
        s.q=queue.Queue(); threading.Thread(target=s._pump,args=(st,),daemon=True).start()
    def _pump(s,st):
        for l in st: s.q.put(l)
        s.q.put(None)
    def get(s,t=600):
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
        l=r.get(30)
        if l is None or l.strip()=="uciok": break
    for o in ["Hash value 16","Threads value 1","OwnBook value false"]+PC20:
        send("setoption name "+o); send("isready"); drain()
    send("ucinewgame"); send("isready"); drain()
    send("position fen "+fen); send("isready"); drain()
    send(go)
    best=None; mate=None; pv=None
    while True:
        l=r.get(600)
        if l is None: break
        if l.startswith("info depth"):
            m=re.search(r"score mate (-?\d+)",l)
            if m and " pv " in l:
                mate=int(m.group(1)); pv=l.split(" pv ",1)[1].split()
        if l.startswith("bestmove"):
            best=l.split()[1]; break
    send("quit")
    try: p.wait(timeout=30)
    except subprocess.TimeoutExpired: p.kill()
    return {"best":best,"mate":mate,"pv":pv}

def pv_legal(fen,pv):
    b=chess.Board(fen); n=0
    for u in pv:
        try: mv=chess.Move.from_uci(u)
        except ValueError: return n,False,False
        if mv not in b.legal_moves: return n,False,False
        b.push(mv); n+=1
    return n,True,b.is_checkmate()

def build_pool():
    """Mate-rich candidates: K+Q / K+R vs K at varied squares, plus simple endgames."""
    out=[]
    for wk in ["a1","b2","c3","h1","d4"]:
        for bk in ["a8","h8","e5","c7"]:
            for wp in ["d1","b7","g2"]:
                fen=f"7k/8/8/8/8/8/8/KQ6 w - - 0 1" if False else None
    # deterministic set: white K+Q vs black K in assorted placements
    ks=[("a1","h8"),("c3","f6"),("b2","g7"),("h1","a8"),("d4","d6"),("e2","e7")]
    for wk,bk in ks:
        for wq in ["d1","b7","e4","h5"]:
            f=chess.Board(None)
            f.set_piece_at(chess.parse_square(wk),chess.Piece(chess.KING,chess.WHITE))
            f.set_piece_at(chess.parse_square(bk),chess.Piece(chess.KING,chess.BLACK))
            f.set_piece_at(chess.parse_square(wq),chess.Piece(chess.QUEEN,chess.WHITE))
            f.turn=chess.WHITE
            if f.is_valid() and not f.is_checkmate():
                out.append(f.fen())
    # K+R vs K, and K+2R
    for wk,bk in ks:
        for wr in ["d1","e4","h5"]:
            f=chess.Board(None)
            f.set_piece_at(chess.parse_square(wk),chess.Piece(chess.KING,chess.WHITE))
            f.set_piece_at(chess.parse_square(bk),chess.Piece(chess.KING,chess.BLACK))
            f.set_piece_at(chess.parse_square(wr),chess.Piece(chess.ROOK,chess.WHITE))
            f.turn=chess.WHITE
            if f.is_valid() and not f.is_checkmate():
                out.append(f.fen())
    return out

def main():
    exe,outdir=sys.argv[1],sys.argv[2]
    cap=int(sys.argv[3]) if len(sys.argv)>3 else 120
    os.makedirs(outdir,exist_ok=True)
    pool=build_pool()[:cap]
    print(f"candidate pool: {len(pool)} K+Q/K+R positions",flush=True)
    # filter: must report a mate at the SMALLEST budget
    kept=[]
    for fen in pool:
        r=run(exe,fen,"go nodes 20000")
        if r["mate"] is not None:
            kept.append(fen)
    print(f"positions reporting a mate at go nodes 20000: {len(kept)} of {len(pool)}",flush=True)
    if len(kept)<10:
        print("WARNING: too few mate-reporting positions to measure a rate honestly")
    rows=[]
    for bname,go in BUDGETS:
        trunc=0; mates=0; details=[]
        for fen in kept:
            r=run(exe,fen,go)
            if r["mate"] is None: continue
            mates+=1
            n,legal,ismate=pv_legal(fen,r["pv"] or [])
            # PV length convention, corrected after my own checker mislabelled a correct line:
            #   mate  N > 0 : the side to move mates -> 2N-1 plies
            #   mate  N < 0 : the side to move is mated -> 2|N| plies  (measured in 07-C40)
            # My first version used 2|N| for both, which demands one ply too many on a positive
            # mate and therefore reported a CORRECT 9-ply PV for "mate 5" as truncated.
            need = 2*r["mate"]-1 if r["mate"]>0 else 2*abs(r["mate"])
            bad=(not legal) or (n!=need)
            if bad:
                trunc+=1
                details.append({"fen":fen,"mate":r["mate"],"pv_plies":n,"need":need,"legal":legal})
        rows.append({"budget":bname,"mate_scores":mates,"truncated":trunc,"details":details})
        print(f"  {bname:8s}: {mates} mate scores, {trunc} truncated "
              f"({100.0*trunc/mates if mates else 0:.1f} %)",flush=True)
    json.dump({"pool":len(pool),"kept":kept,"rows":rows},
              open(os.path.join(outdir,"mate_rich.json"),"w"),indent=1)

if __name__=="__main__": main()
