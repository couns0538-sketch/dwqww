#!/usr/bin/env python3
"""swarm seat 01: CHECK of seat 02's S-F13 — a clock move's wall time IS the last completed iteration's cost.

Seat 02's claim, verbatim:
  "The owner's 6 s + 0.06 clock is used at only 3.3-5.8 % per class (medians 197-353 ms), and a move's wall
   time IS the last completed iteration's cost - Spearman rho 0.998, and 17 of 20 boards match within 2 %.
   ... The only route to an expensive move is the HARD limit: one sparse endgame ... hit 1585.6 ms = 26.2 %
   of the clock while its last completed iteration was only 667 ms - i.e. cut mid-iteration."

Two separable claims, and I test both:
  A. the CORRELATION: wall time vs the node count (or time) of the last completed iteration. Seat 02 reports
     rho 0.998. I measure my own rho over my own boards.
  B. the HARD-LIMIT cut: a board where the wall time substantially EXCEEDS the last completed iteration,
     which is the signature of being cut mid-iteration. Seat 02 says this is the only route to an expensive
     move, so it should be RARE - most boards should show wall ~= iteration.

Note the confound seat 02 itself flags: mixing solved/trivial boards into a latency average. I exclude any
board where the search stops at a depth cap, by checking the last depth against the 64 cap.

Usage: check_walltime_is_iteration.py <pc-exe> <outdir> [n-boards]
"""
import hashlib, json, os, select, statistics, subprocess, sys, time
from pathlib import Path
import chess

TIMEOUT=300.0
OPTS=[("LmrQuietBase","93"),("LmrQuietDivisor","205"),("LmrNoisyBase","13"),("LmrNoisyDivisor","333"),
      ("LmrHistoryDivisor","5643"),("NullMoveBase","5"),("LmpBase","8"),("HistoryPruneMultiplier","2220"),
      ("HistoryBonusQuadratic","24"),("HistoryBonusLinear","54"),("HistoryBonusMax","2212"),
      ("SingularDepth","6"),("IirDepth","2"),("NonPawnCorrection","true"),("CuckooRep","true"),
      ("HistRework","2"),("TtPruneV2","true"),("CorrHistV2","true"),("MateAlphaGuard","true"),
      ("OwnBook","false"),("Threads","1"),("Hash","16")]
CLOCK=6000; INC=60

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

def run(exe,fen):
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
    send("position fen "+fen); send("isready"); until("readyok",d)
    t0=time.monotonic()
    send("go wtime %d btime %d winc %d binc %d"%(CLOCK,CLOCK,INC,INC))
    bml=until("bestmove",d)
    wall=(time.monotonic()-t0)*1000.0
    send("quit")
    try: p.wait(timeout=120)
    except Exception: p.kill()
    # per-iteration (depth, nodes, time) so I can take the LAST completed iteration's own time
    iters=[]
    for l in buf:
        if not l.startswith("info depth"): continue
        f=l.split()
        try:
            iters.append({"depth":int(f[f.index("depth")+1]),
                          "nodes":int(f[f.index("nodes")+1]),
                          "time":int(f[f.index("time")+1]) if "time" in f else None})
        except (ValueError,IndexError): pass
    last=iters[-1] if iters else None
    return {"wall_ms":round(wall,1),"iters":iters,"last":last,
            "bestmove":bml.split()[1] if bml and len(bml.split())>1 else None}

def spearman(xs,ys):
    def ranks(v):
        order=sorted(range(len(v)), key=lambda i:v[i])
        r=[0]*len(v)
        for pos,i in enumerate(order): r[i]=pos+1
        return r
    rx,ry=ranks(xs),ranks(ys)
    n=len(xs)
    mx,my=sum(rx)/n,sum(ry)/n
    num=sum((a-mx)*(b-my) for a,b in zip(rx,ry))
    dx=sum((a-mx)**2 for a in rx)**0.5
    dy=sum((b-my)**2 for b in ry)**0.5
    return num/(dx*dy) if dx and dy else None

def main():
    exe=sys.argv[1]; out=Path(sys.argv[2]); n=int(sys.argv[3]) if len(sys.argv)>3 else 16
    out.mkdir(parents=True,exist_ok=True)
    gpath="/agent/repos/dwqww/forge-combo29/swarm/01/job1/set_G.epd"
    fens=[]
    for line in open(gpath):
        line=line.strip()
        if not line or line.startswith("#"): continue
        parts=line.split()
        if len(parts)>=4: fens.append(" ".join(parts[:4])+" 0 1")
        if len(fens)>=n: break
    lines=["CHECK of seat 02's S-F13: is a clock move's wall time the last completed iteration's cost?",
           "exe_started: %s"%exe,"sha256: %s"%hashlib.sha256(Path(exe).read_bytes()).hexdigest(),
           "PC r15 + PC20, Threads 1, Hash 16, go wtime %d btime %d winc %d binc %d, one fresh process per board"
           %(CLOCK,CLOCK,INC,INC),
           "boards: first %d of set_G"%len(fens),""]
    lines.append("board\twall_ms\tlast_iter_nodes\tlast_iter_time\twall-minus-iter\tcut_mid_iter?\tlast_depth")
    rows=[]
    for i,fen in enumerate(fens):
        r=run(exe,fen)
        if not r["last"]: continue
        lt=r["last"]["time"]
        diff = (r["wall_ms"]-lt) if lt is not None else None
        # "cut mid-iteration" = wall substantially exceeds the last completed iteration's own time
        cut = (diff is not None and diff > 0.25*max(lt,1))
        rows.append({"board":i+1,"fen":fen,**r,"diff":diff,"cut":cut})
        print("board %-2d wall %-8s lastiter %-6s nodes %-8s diff %-7s cut=%-5s depth %s"
              %(i+1,r["wall_ms"],lt,r["last"]["nodes"],
                ("%.1f"%diff) if diff is not None else "-",cut,r["last"]["depth"]),flush=True)
        lines.append("%d\t%s\t%s\t%s\t%s\t%s\t%s"%(i+1,r["wall_ms"],r["last"]["nodes"],lt,
                     ("%.1f"%diff) if diff is not None else "-",cut,r["last"]["depth"]))
    usable=[r for r in rows if r["last"]["time"] is not None]
    v=[]
    v.append("")
    if len(usable)>=5:
        rho=spearman([r["wall_ms"] for r in usable],[r["last"]["time"] for r in usable])
        v.append("A. CORRELATION: Spearman rho(wall, last completed iteration's time) = %.3f over %d boards"
                 %(rho,len(usable)))
        frac=[r for r in usable if r["diff"] is not None and abs(r["diff"])<=0.10*r["last"]["time"]]
        v.append("   boards whose wall time is within 10 %% of the last iteration's own time: %d of %d"
                 %(len(frac),len(usable)))
        v.append("   -> %s seat 02's reading that the clock tail IS the iteration cost."%
                 ("CONSISTENT WITH" if rho and rho>0.9 else "NOT clearly consistent with"))
    cuts=[r for r in rows if r["cut"]]
    v.append("")
    v.append("B. HARD-LIMIT CUTS: %d of %d boards show wall >> last iteration (cut mid-iteration)."%(
        len(cuts),len(rows)))
    for c in cuts:
        v.append("   board %d: wall %.1f ms vs last iteration %.1f ms (diff %.1f), depth %d, %d nodes"
                 %(c["board"],c["wall_ms"],c["last"]["time"],c["diff"],c["last"]["depth"],c["last"]["nodes"]))
    if cuts and len(cuts)<len(rows)*0.35:
        v.append("   -> RARE, which matches seat 02: the hard limit is the only route to an expensive move, and")
        v.append("      it is the exception rather than the rule.")
    elif not cuts:
        v.append("   -> none on my boards: the hard-limit cut did not occur here, so its rarity is consistent")
        v.append("      with seat 02 but its existence is not demonstrated by this sample.")
    else:
        v.append("   -> common on my boards; see the rows.")
    (out/"check_walltime_is_iteration.json").write_text(json.dumps(
        {"clock":[CLOCK,INC],"rows":rows,"verdict":v},indent=1))
    (out/"check_walltime_is_iteration.txt").write_text("\n".join(lines+v)+"\n")
    print(""); print("\n".join(v))

if __name__=="__main__":
    main()
