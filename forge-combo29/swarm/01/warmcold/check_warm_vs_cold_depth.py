#!/usr/bin/env python3
"""swarm seat 01: CHECK of seat 20's S-F51 — a warm process reaches +2 plies at the same clock.

Seat 20's claim, verbatim:
  "On the same cell (clock 6 s + 0.06, MultiPV 1, Hash 16, PC r15 + PC20, Threads 1, 10 G-set positions) a
   fresh process per position gives median depth 18 and one warm process gives median depth 20 - +2 plies at
   the same wall time. This is the same class as the node-count warm/cold rule, now shown to affect DEPTH ...
   since the PC's matches run one process over many moves, WARM is the match-realistic reading."

This matters to my own S-C20, which used a fresh process per board for the clock path. If seat 20 is right, my
cold depths understate what a game sees.

Design, on MY boards (not seat 20's), same clock and settings:
  COLD: one fresh process per position, one search each.
  WARM: ONE process, the same positions searched in the same order, so each search inherits the hash and the
        histories from the previous ones - which is what a game does.
Report per-position depth for both, the medians, and the wall times, so "+2 plies at the same wall time" is
directly checkable rather than inferred.

A subtlety I must control for: in a real game the position CHANGES between moves, so the warm case here
searches DIFFERENT positions in one process, not the same one repeatedly. Repeating one position in a warm
process would test hash reuse on the same key, which is not what a match does.

Usage: check_warm_vs_cold_depth.py <pc-exe> <outdir> [n-boards]
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

def setup(p):
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
    return rd,send,until

def one_cold(exe,fen):
    p=subprocess.Popen([exe],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,bufsize=0,cwd="/tmp")
    rd,send,until=setup(p)
    send("ucinewgame"); send("isready"); until("readyok",time.monotonic()+30)
    send("position fen "+fen); send("isready"); until("readyok",time.monotonic()+30)
    t0=time.monotonic()
    send("go wtime %d btime %d winc %d binc %d"%(CLOCK,CLOCK,INC,INC))
    buf=[]
    dl=[]
    # collect depth lines during this search
    while True:
        l=rd.line(time.monotonic()+TIMEOUT)
        if l is None: break
        if l.startswith("info depth"): dl.append(l)
        if l.startswith("bestmove"): break
    wall=(time.monotonic()-t0)*1000
    send("quit")
    try: p.wait(timeout=30)
    except Exception: p.kill()
    depth=None
    for l in reversed(dl):
        f=l.split()
        if "depth" in f: depth=int(f[f.index("depth")+1]); break
    return {"depth":depth,"wall_ms":round(wall,1)}

def warm_series(exe,fens):
    """ONE process; search each position in order, so each search inherits the previous ones."""
    p=subprocess.Popen([exe],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,bufsize=0,cwd="/tmp")
    rd,send,until=setup(p)
    send("ucinewgame"); send("isready"); until("readyok",time.monotonic()+30)
    out=[]
    for fen in fens:
        send("position fen "+fen); send("isready"); until("readyok",time.monotonic()+30)
        t0=time.monotonic()
        send("go wtime %d btime %d winc %d binc %d"%(CLOCK,CLOCK,INC,INC))
        dl=[]
        while True:
            l=rd.line(time.monotonic()+TIMEOUT)
            if l is None: break
            if l.startswith("info depth"): dl.append(l)
            if l.startswith("bestmove"): break
        wall=(time.monotonic()-t0)*1000
        depth=None
        for l in reversed(dl):
            f=l.split()
            if "depth" in f: depth=int(f[f.index("depth")+1]); break
        out.append({"depth":depth,"wall_ms":round(wall,1)})
    send("quit")
    try: p.wait(timeout=30)
    except Exception: p.kill()
    return out

def main():
    exe=sys.argv[1]; out=Path(sys.argv[2]); n=int(sys.argv[3]) if len(sys.argv)>3 else 10
    out.mkdir(parents=True,exist_ok=True)
    fens=[]
    for line in open("/agent/repos/dwqww/forge-combo29/swarm/01/job1/set_G.epd"):
        line=line.strip()
        if not line or line.startswith("#"): continue
        parts=line.split()
        if len(parts)>=4: fens.append(" ".join(parts[:4])+" 0 1")
        if len(fens)>=n: break
    lines=["CHECK of seat 20's S-F51: does a WARM process reach +2 plies at the same clock?",
           "exe_started: %s"%exe,"sha256: %s"%hashlib.sha256(Path(exe).read_bytes()).hexdigest(),
           "PC r15 + PC20, Threads 1, Hash 16, go wtime %d btime %d winc %d binc %d"%(CLOCK,CLOCK,INC,INC),
           "COLD = fresh process per position; WARM = one process, same positions in the same order",
           "boards: first %d of set_G"%len(fens),""]
    cold=[one_cold(exe,f) for f in fens]
    for i,c in enumerate(cold): print("cold %-2d depth %-3s wall %-8s"%(i+1,c["depth"],c["wall_ms"]),flush=True)
    warm=warm_series(exe,fens)
    for i,c in enumerate(warm): print("warm %-2d depth %-3s wall %-8s"%(i+1,c["depth"],c["wall_ms"]),flush=True)
    lines.append("board\tcold_depth\tcold_wall\twarm_depth\twarm_wall\tdepth_delta")
    for i,(c,w) in enumerate(zip(cold,warm)):
        lines.append("%d\t%s\t%s\t%s\t%s\t%s"%(i+1,c["depth"],c["wall_ms"],w["depth"],w["wall_ms"],
                     (w["depth"]-c["depth"]) if (c["depth"] is not None and w["depth"] is not None) else "-"))
    cd=[c["depth"] for c in cold if c["depth"] is not None]
    wd=[w["depth"] for w in warm if w["depth"] is not None]
    cw=[c["wall_ms"] for c in cold]
    ww=[w["wall_ms"] for w in warm]
    v=[]
    v.append("")
    v.append("COLD: median depth %s, median wall %.0f ms (n=%d)"%(statistics.median(cd),statistics.median(cw),len(cd)))
    v.append("WARM: median depth %s, median wall %.0f ms (n=%d)"%(statistics.median(wd),statistics.median(ww),len(wd)))
    delta=statistics.median(wd)-statistics.median(cd)
    v.append("DEPTH DELTA (warm - cold): %+.0f plies at a wall difference of %+.0f ms"%(delta,statistics.median(ww)-statistics.median(cw)))
    v.append("")
    if delta>=1 and abs(statistics.median(ww)-statistics.median(cw)) < 0.25*statistics.median(cw):
        v.append("VERDICT: CONFIRMS seat 20's S-F51. A warm process reaches MORE plies at essentially the same")
        v.append("  wall time, so a cold-process depth table understates what a match sees. My own S-C20 used a")
        v.append("  fresh process per board and therefore reports COLD depths - correct for its question, but")
        v.append("  the match-realistic figure is the warm one, and I label it so.")
    elif delta>=1:
        v.append("VERDICT: warm reaches more plies, but its wall time differs by more than 25 %, so 'at the same")
        v.append("  wall time' does not hold here; reported as is.")
    else:
        v.append("VERDICT: no depth advantage for the warm process on my boards; does NOT reproduce S-F51.")
    (out/"check_warm_vs_cold_depth.json").write_text(json.dumps(
        {"clock":[CLOCK,INC],"cold":cold,"warm":warm,"verdict":v},indent=1))
    (out/"check_warm_vs_cold_depth.txt").write_text("\n".join(lines+v)+"\n")
    print(""); print("\n".join(v))

if __name__=="__main__":
    main()
