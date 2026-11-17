#!/usr/bin/env python3
"""check_28sf44.py -- does the clock rule have a fixed-point floor at 110 ms, independent of start?

Seat 28's S-F44: with `clock' = clock - spend + increment` and the search capped at
hard = min((clock - MoveOverhead)*TmHardPercent/100, soft*TmHardSoftMultiple), the floor is
MoveOverhead + increment*100/TmHardPercent = 10 + 60*100/60 = 110 ms, and iterating with worst-case
spend converges to 111 ms from EVERY starting clock.

Check two ways:
  A. ARITHMETIC (exact, from include/forge/clock_plan.hpp's own formulas, re-implemented here):
     iterate the real rule with spend = hard, from many starting clocks, and report the fixed point.
  B. ENGINE (behavioural): with a 60 ms increment, does a search's spend ever exceed its increment?
     If spend <= increment then the clock never decreases, so the floor must be at or above the
     starting clock -- the opposite of a floor at 110 ms. Measure spend for several clocks.

A fixed-point claim is arithmetic, so A is the load-bearing check; B says whether the engine's real
spend respects the assumption the floor relies on.
"""
import json, os, queue, re, subprocess, sys, threading, time

S14=["LmrQuietBase value 93","LmrQuietDivisor value 205","LmrNoisyBase value 13",
 "LmrNoisyDivisor value 333","LmrHistoryDivisor value 5643","NullMoveBase value 5","LmpBase value 8",
 "HistoryPruneMultiplier value 2220","HistoryBonusQuadratic value 24","HistoryBonusLinear value 54",
 "HistoryBonusMax value 2212","SingularDepth value 6","IirDepth value 2","NonPawnCorrection value true"]
PC20=S14+["CuckooRep value true","HistRework value 2","TtPruneV2 value true",
 "CorrHistV2 value true","MateAlphaGuard value true","OwnBook value false"]
FEN="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"

# PC20 tunables from the source defaults (search.cpp tune:: block)
SOFT_DIV=22; INC_PCT=75; HARD_PCT=60; HARD_SOFT_MULT=5; OVERHEAD=10

def plan(clock, inc):
    """Re-implement plan_clock_budget exactly as include/forge/clock_plan.hpp does."""
    overhead=max(0,OVERHEAD); t=max(0,clock); i=max(0,inc)
    if t<=overhead: return 0,0,True
    avail=t-overhead
    soft=avail//SOFT_DIV + i*INC_PCT//100
    hard=min(avail*HARD_PCT//100, soft*HARD_SOFT_MULT)
    soft=max(1,min(soft,avail)); hard=max(1,min(hard,avail))
    if soft>hard: soft=hard
    return soft,hard,False

def iterate(start, inc, worst=True):
    c=start; seen=[]
    for _ in range(200):
        soft,hard,empty=plan(c,inc)
        if empty: return 0,seen
        spend = hard if worst else soft
        c = c - spend + inc
        seen.append(c)
        if c<=0: return 0,seen
    return c,seen

class R:
    def __init__(s,st):
        s.q=queue.Queue(); threading.Thread(target=s._pump,args=(st,),daemon=True).start()
    def _pump(s,st):
        for l in st: s.q.put(l)
        s.q.put(None)
    def get(s,t=12000):
        try: return s.q.get(timeout=t)
        except queue.Empty: return None

def engine_spend(exe,clock,inc):
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
    t0=time.monotonic(); send(f"go wtime {clock} btime {clock} winc {inc} binc {inc}")
    while True:
        l=r.get(12000)
        if l is None: break
        if l.startswith("bestmove"): break
    wall=(time.monotonic()-t0)*1000.0
    send("quit")
    try: p.wait(timeout=30)
    except subprocess.TimeoutExpired: p.kill()
    return wall

def main():
    exe,outdir=sys.argv[1],sys.argv[2]
    os.makedirs(outdir,exist_ok=True)
    INC=60
    print(f"A. ARITHMETIC: iterate clock' = clock - spend + increment, increment {INC} ms, spend = hard")
    rows=[]
    for start in (6000,3000,1000,500,300,200,150,120,115,111,110,109):
        c,seq=iterate(start,INC)
        rows.append({"start":start,"fixed_point":c})
        print(f"   start {start:>5} -> fixed point {c:>5} ms   (first 4 iterates {seq[:4]})",flush=True)
    print()
    print(f"B. ENGINE: actual spend with a {INC} ms increment (wall clock), vs the increment")
    eng=[]
    for clock in (6000,1000,300,150):
        w=engine_spend(exe,clock,INC)
        eng.append({"clock":clock,"spend_ms":round(w,1)})
        print(f"   clock {clock:>5}: spend {w:>8.1f} ms  {'EXCEEDS increment' if w>INC else 'within increment'}",flush=True)
    json.dump({"arithmetic":rows,"engine":eng,"increment":INC},
              open(os.path.join(outdir,"check_28sf44.json"),"w"),indent=1)

    fixed=[r["fixed_point"] for r in rows if r["start"]>=111]
    print()
    if len(set(fixed))==1:
        print(f"=> fixed point is the SAME ({fixed[0]} ms) from every start >= 111 -> a genuine floor")
    else:
        print(f"=> fixed points differ across starts ({sorted(set(fixed))}) -> not a single floor")

if __name__=="__main__": main()
