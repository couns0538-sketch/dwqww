#!/usr/bin/env python3
"""check_16sf28.py -- does an IDENTICAL 6000 ms clock buy an inconsistent effort?

Seat 16's S-F28: across a game-shaped move sequence at a constant 6 s clock on the PC build under PC20,
Threads 1, the engine never overruns, but its own reported search time ranges 166-416 ms -- a 2.51x ratio
over ten moves -- so "6 s per move" does not buy a consistent effort.

My check: play a short sequence from ONE real position, re-sending `go wtime 6000 btime 6000 winc 60 binc 60`
with a CONSTANT clock (no decrement, so the budget is identical every move), and record the engine's own
`time` field and the wall time per move. Report the range, the ratio, and whether any move overran.

Also measures the RATIO against the budget (to pair with 07-C50's 6 % utilisation figure).

Controls: (a) the sequence must actually alternate moves; (b) a `go movetime 6000` interleaved must run
~6000 ms and must NOT leak into the next clock search (seat 16's second claim).
"""
import json, os, queue, re, subprocess, sys, threading, time
import chess

S14=["LmrQuietBase value 93","LmrQuietDivisor value 205","LmrNoisyBase value 13",
 "LmrNoisyDivisor value 333","LmrHistoryDivisor value 5643","NullMoveBase value 5","LmpBase value 8",
 "HistoryPruneMultiplier value 2220","HistoryBonusQuadratic value 24","HistoryBonusLinear value 54",
 "HistoryBonusMax value 2212","SingularDepth value 6","IirDepth value 2","NonPawnCorrection value true"]
PC20=S14+["CuckooRep value true","HistRework value 2","TtPruneV2 value true",
 "CorrHistV2 value true","MateAlphaGuard value true","OwnBook value false"]
START="r1bq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N1PN2/PP3PPP/R2QKB1R w KQ - 0 8"

class R:
    def __init__(s,st):
        s.q=queue.Queue(); threading.Thread(target=s._pump,args=(st,),daemon=True).start()
    def _pump(s,st):
        for l in st: s.q.put(l)
        s.q.put(None)
    def get(s,t=12000):
        try: return s.q.get(timeout=t)
        except queue.Empty: return None

def main():
    exe,outdir=sys.argv[1],sys.argv[2]
    moves=int(sys.argv[3]) if len(sys.argv)>3 else 10
    os.makedirs(outdir,exist_ok=True)
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

    b=chess.Board(START)
    rows=[]
    # interleave one movetime search after move 3 to test for leakage
    for i in range(moves):
        send("ucinewgame"); send("isready"); drain()
        send("position fen "+b.fen()); send("isready"); drain()
        go="go wtime 6000 btime 6000 winc 60 binc 60"
        if i==3:
            go="go movetime 6000"
        t0=time.monotonic(); send(go)
        engtime=None;best=None
        while True:
            l=r.get(12000)
            if l is None: break
            if l.startswith("info depth"):
                m=re.search(r" time (\d+) ",l+" ")
                if m: engtime=int(m.group(1))
            if l.startswith("bestmove"):
                best=l.split()[1]; break
        wall=(time.monotonic()-t0)*1000.0
        rows.append({"i":i,"go":go,"eng_ms":engtime,"wall_ms":round(wall,1),"best":best,"fen":b.fen()})
        print(f"  move {i:>2} {'movetime' if i==3 else 'clock   '}: eng {str(engtime):>5} ms  wall {wall:>8.1f} ms  {best}",flush=True)
        try: b.push(chess.Move.from_uci(best))
        except Exception: break
    send("quit")
    try: p.wait(timeout=30)
    except subprocess.TimeoutExpired: p.kill()
    json.dump(rows,open(os.path.join(outdir,"check_16sf28.json"),"w"),indent=1)

    clock=[r for r in rows if "wtime" in r["go"]]
    if clock:
        vals=[r["eng_ms"] for r in clock if r["eng_ms"] is not None]
        walls=[r["wall_ms"] for r in clock]
        print()
        print(f"CLOCK moves: {len(clock)}")
        print(f"  engine time  min {min(vals)} max {max(vals)} ratio {max(vals)/min(vals):.2f}x")
        print(f"  wall time    min {min(walls):.0f} max {max(walls):.0f}")
        print(f"  overruns (wall > 6000): {sum(1 for w in walls if w > 6000)}")
        print(f"  utilisation of 6000 ms: median {sorted(walls)[len(walls)//2]/6000*100:.1f} % "
              f"max {max(walls)/6000*100:.1f} %")
    mv=[r for r in rows if "movetime" in r["go"]]
    if mv:
        print(f"MOVETIME move: wall {mv[0]['wall_ms']} ms (should be ~6000)")
        after=[r for r in rows if r["i"]>3 and "wtime" in r["go"]]
        if after:
            print(f"  next clock move after movetime: eng {after[0]['eng_ms']} ms wall {after[0]['wall_ms']} ms "
                  f"-> leakage {'YES' if after[0]['wall_ms']>3000 else 'no'}")

if __name__=="__main__": main()
