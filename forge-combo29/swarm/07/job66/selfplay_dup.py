#!/usr/bin/env python3
"""selfplay_dup.py -- do self-play games from ONE start duplicate, and does varying the start fix it?

Seat 16's S-F27 / S-F29 claim:
  S-F27: ten games from the SAME start give only THREE distinct final positions (7 of 10 identical),
         because the engine is deterministic at Threads 1 with fixed limits.
  S-F29: ten games from ten DIFFERENT starts give TEN distinct final positions and move sequences.

Their runs used a clock (6 s + 0.06), where millisecond drift can break determinism. I use a NODE
budget (`go nodes 20000`) instead, because 07-C49 showed node stops are exactly reproducible here --
so this isolates the determinism question from clock jitter. If the claim is about determinism rather
than clock drift, node-budget self-play should duplicate even MORE reliably from one start.

Two arms, 10 games each, 40 plies:
  FIXED  : all ten games from startpos
  VARIED : the ten games from ten different real-G positions
Report distinct final positions, distinct move sequences, illegal moves, and any duplicate games.
"""
import json, os, queue, subprocess, sys, threading
import chess

S14=["LmrQuietBase value 93","LmrQuietDivisor value 205","LmrNoisyBase value 13",
 "LmrNoisyDivisor value 333","LmrHistoryDivisor value 5643","NullMoveBase value 5","LmpBase value 8",
 "HistoryPruneMultiplier value 2220","HistoryBonusQuadratic value 24","HistoryBonusLinear value 54",
 "HistoryBonusMax value 2212","SingularDepth value 6","IirDepth value 2","NonPawnCorrection value true"]
PC20=S14+["CuckooRep value true","HistRework value 2","TtPruneV2 value true",
 "CorrHistV2 value true","MateAlphaGuard value true","OwnBook value false"]
START=chess.Board().fen()

class R:
    def __init__(s,st):
        s.q=queue.Queue(); threading.Thread(target=s._pump,args=(st,),daemon=True).start()
    def _pump(s,st):
        for l in st: s.q.put(l)
        s.q.put(None)
    def get(s,t=600):
        try: return s.q.get(timeout=t)
        except queue.Empty: return None

def bestmove(exe,fen):
    p=subprocess.Popen([exe],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True,bufsize=1)
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
    for o in ["Hash value 16","Threads value 1","OwnBook value false"]+PC20:
        send("setoption name "+o); send("isready"); drain()
    send("ucinewgame"); send("isready"); drain()
    send("position fen "+fen); send("isready"); drain()
    send("go nodes 20000")
    best=None
    while True:
        l=r.get(600)
        if l is None: break
        if l.startswith("bestmove"):
            best=l.split()[1]; break
    send("quit")
    try: p.wait(timeout=20)
    except subprocess.TimeoutExpired: p.kill()
    if best is None: raise SystemExit("FAIL no bestmove")
    return best

def play(exe,start_fen,plies=40):
    b=chess.Board(start_fen); seq=[]; illegal=0
    for _ in range(plies):
        if b.is_game_over(): break
        mv=bestmove(exe,b.fen())
        try: m=chess.Move.from_uci(mv)
        except ValueError: illegal+=1; break
        if m not in b.legal_moves: illegal+=1; break
        b.push(m); seq.append(mv)
    return {"final":b.fen(),"seq":" ".join(seq),"illegal":illegal}

def main():
    exe,outdir=sys.argv[1],sys.argv[2]
    plies=int(sys.argv[3]) if len(sys.argv)>3 else 40
    os.makedirs(outdir,exist_ok=True)
    # ten real-G starts for the VARIED arm
    g=[]
    for line in open('/tmp/set_G.epd',encoding='utf-8'):
        p=line.split()
        if len(p)>=4:
            f=" ".join(p[:6]) if len(p)>=6 else " ".join(p[:4])+" 0 1"
            try: chess.Board(f)
            except ValueError: continue
            g.append(f)
    varied_starts=g[:10]
    out={}
    for arm,starts in (("FIXED",[START]*10),("VARIED",varied_starts)):
        games=[]
        for i,s in enumerate(starts):
            r=play(exe,s,plies); games.append(r)
            print(f"  {arm} game {i}: {len(r['seq'].split())} plies, illegal {r['illegal']}, "
                  f"final {r['final'][:40]}",flush=True)
        finals={x["final"] for x in games}; seqs={x["seq"] for x in games}
        out[arm]={"distinct_finals":len(finals),"distinct_sequences":len(seqs),
                  "illegal_total":sum(x["illegal"] for x in games),"games":games}
        print(f"{arm}: {len(finals)} distinct final positions, {len(seqs)} distinct sequences "
              f"of 10 games",flush=True)
    json.dump(out,open(os.path.join(outdir,"selfplay_dup.json"),"w"),indent=1)
    print()
    print("seat 16: FIXED 3 distinct finals (7 of 10 identical); VARIED 10 distinct finals and sequences.")
    f=out["FIXED"]; v=out["VARIED"]
    print(f"mine  : FIXED {f['distinct_finals']} finals / {f['distinct_sequences']} sequences; "
          f"VARIED {v['distinct_finals']} finals / {v['distinct_sequences']} sequences")

if __name__=="__main__": main()
