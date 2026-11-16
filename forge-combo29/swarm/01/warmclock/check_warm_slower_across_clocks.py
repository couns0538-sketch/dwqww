#!/usr/bin/env python3
"""swarm seat 01: does the WARM-slows-down effect hold at other clocks, or is it a 6 s artefact?

My S-F74 found, at the owner's 6 s + 0.06 clock, that the warm policy (one reused process per game) costs
MORE per move than a cold one: 156.9 ms against 129.2 ms, because the warm process reaches greater depth and
the extra depth costs more than the reused hash saves.

One clock is not a law. If warm is slower only at 6 s, then the effect is about having ENOUGH time to reach
depths where the table matters; at a short clock both policies should stop at similar depths and the warm
advantage (or penalty) should shrink. So this measures the same comparison at four clocks.

Design: for each clock, warm = one process playing a short sequence of DIFFERENT positions (like a game);
cold = one fresh process per position, same positions, same order. Report per-position wall and depth for both,
and the medians, so the effect can be read as a function of the clock.

Note the deliberate improvement over S-F74: both arms use the SAME positions in the SAME order, so the only
difference is process policy. S-F74 compared two different games, which confounded policy with position.

Usage: check_warm_slower_across_clocks.py <pc-exe> <outdir>
"""
import hashlib, json, os, select, statistics, subprocess, sys, time
from pathlib import Path

TIMEOUT=300.0
OPTS=[("LmrQuietBase","93"),("LmrQuietDivisor","205"),("LmrNoisyBase","13"),("LmrNoisyDivisor","333"),
      ("LmrHistoryDivisor","5643"),("NullMoveBase","5"),("LmpBase","8"),("HistoryPruneMultiplier","2220"),
      ("HistoryBonusQuadratic","24"),("HistoryBonusLinear","54"),("HistoryBonusMax","2212"),
      ("SingularDepth","6"),("IirDepth","2"),("NonPawnCorrection","true"),("CuckooRep","true"),
      ("HistRework","2"),("TtPruneV2","true"),("CorrHistV2","true"),("MateAlphaGuard","true"),
      ("OwnBook","false"),("Threads","1"),("Hash","16")]
INC=60
CLOCKS=[6000,2000,1000,300]

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

def mk_session(exe):
    p=subprocess.Popen([exe],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,bufsize=0,cwd="/tmp")
    rd=R(p.stdout.fileno())
    def until(pre,dl):
        while True:
            l=rd.line(dl)
            if l is None: return None
            if l.startswith(pre): return l
    def send(s): p.stdin.write((s+"\n").encode()); p.stdin.flush()
    d=time.monotonic()+60
    send("uci"); until("uciok",d)
    for n,v in OPTS: send("setoption name %s value %s"%(n,v)); send("isready"); until("readyok",d)
    send("ucinewgame"); send("isready"); until("readyok",d)
    return p,rd,until,send

def go(exe, sess, fen, clock):
    if sess is None:
        p,rd,until,send=mk_session(exe)
    else:
        p,rd,until,send=sess
    d=time.monotonic()+60
    send("position fen "+fen); send("isready"); until("readyok",d)
    t0=time.monotonic()
    send("go wtime %d btime %d winc %d binc %d"%(clock,clock,INC,INC))
    dl=[]
    bm=None
    while True:
        l=rd.line(time.monotonic()+TIMEOUT)
        if l is None: break
        if l.startswith("info depth"): dl.append(l)
        if l.startswith("bestmove"):
            bm=l.split()[1] if len(l.split())>1 else None; break
    wall=(time.monotonic()-t0)*1000.0
    depth=None; nodes=None
    for l in reversed(dl):
        f=l.split()
        if depth is None and "depth" in f: depth=int(f[f.index("depth")+1])
        if nodes is None and "nodes" in f: nodes=int(f[f.index("nodes")+1])
        if depth is not None and nodes is not None: break
    if sess is None:
        send("quit")
        try: p.wait(timeout=30)
        except Exception: p.kill()
    return {"depth":depth,"nodes":nodes,"wall_ms":round(wall,1),"bestmove":bm}

def main():
    exe=sys.argv[1]; out=Path(sys.argv[2]); out.mkdir(parents=True,exist_ok=True)
    fens=[]
    for line in open("/agent/repos/dwqww/forge-combo29/swarm/01/job1/set_G.epd"):
        line=line.strip()
        if not line or line.startswith("#"): continue
        parts=line.split()
        if len(parts)>=4: fens.append(" ".join(parts[:4])+" 0 1")
        if len(fens)>=6: break
    lines=["warm vs cold per-move cost ACROSS CLOCKS - both arms on the SAME positions in the SAME order,",
           "so the only difference is process policy (this fixes S-F74's confound, which compared two games)",
           "exe_started: %s"%exe,"sha256: %s"%hashlib.sha256(Path(exe).read_bytes()).hexdigest(),
           "PC20, Threads 1, Hash 16, winc=binc=60, %d positions"%len(fens),""]
    lines.append("clock\tcold_med_wall\tcold_med_depth\twarm_med_wall\twarm_med_depth\twarm/cold wall\twarm/cold depth")
    rows=[]
    for clock in CLOCKS:
        cold=[go(exe,None,f,clock) for f in fens]
        sess=mk_session(exe)
        warm=[go(exe,sess,f,clock) for f in fens]
        sess[3]("quit")
        try: sess[0].wait(timeout=30)
        except Exception: sess[0].kill()
        cw=statistics.median([c["wall_ms"] for c in cold])
        ww=statistics.median([w["wall_ms"] for w in warm])
        cd=statistics.median([c["depth"] for c in cold if c["depth"] is not None])
        wd=statistics.median([w["depth"] for w in warm if w["depth"] is not None])
        ratio=ww/cw if cw else None
        dratio=wd/cd if cd else None
        rows.append({"clock":clock,"cold_med_wall":cw,"warm_med_wall":ww,"cold_med_depth":cd,
                     "warm_med_depth":wd,"wall_ratio":round(ratio,3) if ratio else None,
                     "depth_ratio":round(dratio,3) if dratio else None,"cold":cold,"warm":warm})
        print("clock %-5d cold %-7.1f d%-3s | warm %-7.1f d%-3s | wall x%.2f depth x%.2f"
              %(clock,cw,cd,ww,wd,ratio or 0,dratio or 0),flush=True)
        lines.append("%d\t%.1f\t%s\t%.1f\t%s\t%.3f\t%.3f"%(clock,cw,cd,ww,wd,ratio or 0,dratio or 0))
    v=[]
    v.append("")
    slower=[r for r in rows if r["wall_ratio"] and r["wall_ratio"]>1.05]
    faster=[r for r in rows if r["wall_ratio"] and r["wall_ratio"]<0.95]
    v.append("RESULT across clocks %s: warm is slower at %d, comparable at %d, faster at %d."
             %(CLOCKS,len(slower),len(rows)-len(slower)-len(faster),len(faster)))
    for r in rows:
        v.append("  clock %-5d warm/cold wall x%.2f (warm %.1f vs cold %.1f ms), depth x%.2f (%s vs %s)"
                 %(r["clock"],r["wall_ratio"] or 0,r["warm_med_wall"],r["cold_med_wall"],
                   r["depth_ratio"] or 0,r["warm_med_depth"],r["cold_med_depth"]))
    v.append("")
    if len(slower)==len(rows):
        v.append("VERDICT: S-F74 GENERALISES - warm is slower per move at EVERY clock tested, so a cold")
        v.append("  benchmark understates per-move cost at any time control, not only at 6 s.")
    elif slower and not faster:
        v.append("VERDICT: warm is slower or comparable at every clock, slower at %d - so S-F74 holds where"
                 %len(slower))
        v.append("  there is enough time to reach depth, and the effect is bounded by the clock. Reported per clock.")
    else:
        v.append("VERDICT: the effect REVERSES at short clocks (warm faster), so S-F74 is a 6 s result, not a law;")
        v.append("  a cold benchmark understates cost only at the longer controls. Reported as is.")
    (out/"check_warm_slower_across_clocks.json").write_text(json.dumps({"rows":rows,"verdict":v},indent=1))
    (out/"check_warm_slower_across_clocks.txt").write_text("\n".join(lines+v)+"\n")
    print(""); print("\n".join(v))

if __name__=="__main__":
    main()
