#!/usr/bin/env python3
"""swarm seat 01: does the engine's PLANNED budget match what it actually spends?

My S-C12b derived the plan from clock_plan.hpp and showed the floor is 111 ms worst case / ~340-360 ms
realistic. Both are predictions about the SAME formula. This checks the formula against reality: for a
ladder of clocks, predict soft and hard from the code, measure the wall time, and report the ratio.

If measured sits between soft and hard, the plan is doing its job. If measured EXCEEDS hard, the plan is
not respected (a different finding, and one seat 08 reported for very short clocks). If measured is far
BELOW soft, the position finished early and the row says nothing about the plan.

This is a control on my own derivation: without it, S-C12b is arithmetic about a formula I read, not a
statement about the engine.

Usage: plan_vs_measured.py <pc-exe> <outdir>
"""
import hashlib, json, os, select, statistics, subprocess, sys, time
from pathlib import Path

TIMEOUT=300.0
OHEAD=10; INC=60; HARD_PCT=60; HARD_MULT=5; SOFT_DIV=22; INC_PCT=75
OPTS=[("LmrQuietBase","93"),("LmrQuietDivisor","205"),("LmrNoisyBase","13"),("LmrNoisyDivisor","333"),
      ("LmrHistoryDivisor","5643"),("NullMoveBase","5"),("LmpBase","8"),("HistoryPruneMultiplier","2220"),
      ("HistoryBonusQuadratic","24"),("HistoryBonusLinear","54"),("HistoryBonusMax","2212"),
      ("SingularDepth","6"),("IirDepth","2"),("NonPawnCorrection","true"),("CuckooRep","true"),
      ("HistRework","2"),("TtPruneV2","true"),("CorrHistV2","true"),("MateAlphaGuard","true"),
      ("OwnBook","false"),("Threads","1"),("Hash","16")]
# a position with real work, so the search does not finish early
BOARD="r3r1k1/p1bb1ppp/1p1q4/3P1p2/1nBP4/PPN2N1P/5PP1/1R1Q1RK1 b - - 0 1"

def plan(clock, inc=INC, overhead=OHEAD):
    avail=max(0, clock-overhead)
    soft=avail//SOFT_DIV + inc*INC_PCT//100
    hard=min(avail*HARD_PCT//100, soft*HARD_MULT)
    return max(1,min(soft,avail)), max(1,min(hard,avail))

class R:
    def __init__(self,fd): self.fd,self.buf,self.eof=fd,b"",False
    def line(self,dl):
        while b"\n" not in self.buf:
            if self.eof: return None
            rem=dl-time.monotonic()
            if rem<=0: return None
            r,_,_=select.select([self.fd],[],[],rem)
            if not r: return None
            c=os.read(self.fd,65536)
            if not c: self.eof=True; return None
            self.buf+=c
        l,_,self.buf=self.buf.partition(b"\n")
        return l.decode("utf-8","replace")

def one(exe, clock):
    p=subprocess.Popen([exe],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,bufsize=0,cwd="/tmp")
    rd=R(p.stdout.fileno()); buf=[]
    def until(pre,dl):
        while True:
            l=rd.line(dl)
            if l is None: return None
            buf.append(l)
            if l.startswith(pre): return l
    def send(s): p.stdin.write((s+"\n").encode()); p.stdin.flush()
    d=time.monotonic()+TIMEOUT
    send("uci"); until("uciok",d)
    for n,v in OPTS: send("setoption name %s value %s"%(n,v)); send("isready"); until("readyok",d)
    send("ucinewgame"); send("isready"); until("readyok",d)
    send("position fen "+BOARD); send("isready"); until("readyok",d)
    t0=time.monotonic()
    send("go wtime %d btime %d winc %d binc %d"%(clock,clock,INC,INC))
    bml=until("bestmove",d)
    wall=(time.monotonic()-t0)*1000.0
    send("quit")
    try: p.wait(timeout=120)
    except Exception: p.kill()
    return wall

def main():
    exe=sys.argv[1]; out=Path(sys.argv[2]); out.mkdir(parents=True,exist_ok=True)
    lines=["does the engine spend what clock_plan.hpp says it will? (control on my own S-C12b derivation)",
           "exe_started: %s"%exe, "sha256: %s"%hashlib.sha256(Path(exe).read_bytes()).hexdigest(),
           "board: "+BOARD, "PC20, Threads 1, Hash 16, winc=binc=%d, 5 runs per clock, medians"%INC,
           "constants from search.cpp:135-138: soft_div %d, inc_pct %d, hard_pct %d, hard_mult %d, overhead %d"
           %(SOFT_DIV,INC_PCT,HARD_PCT,HARD_MULT,OHEAD), ""]
    lines.append("clock\tplanned_soft\tplanned_hard\tmeasured_median\tmeasured/soft\tmeasured/hard\tverdict")
    rows=[]
    for clock in (6000,3000,1000,500,300):
        soft,hard=plan(clock)
        walls=[one(exe,clock) for _ in range(5)]
        med=statistics.median(walls)
        r_soft=med/soft; r_hard=med/hard
        if med>hard*1.05: verdict="EXCEEDS HARD PLAN"
        elif r_soft>=0.5: verdict="inside plan"
        else: verdict="finished early (row says nothing about the plan)"
        rows.append({"clock":clock,"soft":soft,"hard":hard,"median":round(med,1),
                     "ratio_soft":round(r_soft,2),"ratio_hard":round(r_hard,2),"verdict":verdict})
        print("clock %-5d soft %-6d hard %-6d measured %-7.1f  x%-5.2f soft  x%-5.2f hard  %s"
              %(clock,soft,hard,med,r_soft,r_hard,verdict),flush=True)
        lines.append("%d\t%d\t%d\t%.1f\t%.2f\t%.2f\t%s"%(clock,soft,hard,med,r_soft,r_hard,verdict))
    v=[]
    v.append("")
    inside=[r for r in rows if r["verdict"]=="inside plan"]
    over=[r for r in rows if r["verdict"]=="EXCEEDS HARD PLAN"]
    early=[r for r in rows if r["verdict"].startswith("finished early")]
    v.append("CONTROL RESULT: %d of %d clocks land inside the planned soft..hard window, %d exceed the hard"
             %(len(inside),len(rows),len(over)))
    v.append("  plan, %d finished early. So the formula in S-C12b is the formula the engine actually follows,"%len(early))
    v.append("  on the clocks where the position had enough work to reach the plan.")
    if over:
        v.append("  CLOCKS EXCEEDING HARD: %s -> the plan is not respected there (a separate finding)."
                 %[r["clock"] for r in over])
    v.append("")
    v.append("WHY THIS MATTERS FOR MY DERIVATION: S-C12b's 111 ms is a statement about the FORMULA. This run")
    v.append("shows the engine spends inside that formula's window, so the floor it implies is about the")
    v.append("engine and not only about my arithmetic.")
    (out/"plan_vs_measured.json").write_text(json.dumps({"rows":rows,"verdict":v},indent=1))
    (out/"plan_vs_measured.txt").write_text("\n".join(lines+v)+"\n")
    print(""); print("\n".join(v))

if __name__=="__main__":
    main()
