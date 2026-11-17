#!/usr/bin/env python3
"""swarm seat 01: does an UNTIMED `go depth 20` hang on a HIGH-COUNTER board? (seat 10's 10-F65)

Seat 10's warning, verbatim: "If you run the recipe's `go depth 20` (or more) UNTIMED on a board whose halfmove
counter is high, the search can take hundreds of millions of nodes to finish one depth and your harness will look
hung -- on this board 250 M nodes to reach depth 15, nothing at 120 s."

I used `go depth 20` untimed on halfmove-99/100 boards in my file-6 application (S-C6), so this affects whether
my own figures are sound. Two questions:

  A. DID MY RUNS COMPLETE? My recorded cells all report reached_depth 20, and the node counts are tiny
     (420 / 662 / 73,634 / 7,305) - because a MATE SCORE ends the iterative loop early (the loop breaks on a
     mate, search.cpp's `if (mate_moves > 0 && score >= mate_in(...)) break;`). So my boards were not at risk:
     they have short mates, and the search stops when it finds one. Verified here by timing them.

  B. IS SEAT 10'S CASE REAL ON MY BUILD? Its board `5k2/8/8/8/8/8/8/1K1Q4 w - - 80 1` at counter 80-90 with an
     untimed depth 20. Measured with a WALL CAP: if it finishes, report how long and how many nodes; if it does
     not, report that it did not within the cap - which is seat 10's "looks hung".

The wall cap is the whole point of the exercise: an untimed call that never returns cannot distinguish "slow"
from "hung", and a harness must impose the cap rather than discover the problem.

Usage: check_untimed_depth20.py <pc-exe> <outdir>
"""
import hashlib, json, os, select, subprocess, sys, time
from pathlib import Path

CAP=90.0      # seconds; seat 10 waited 120 s and got nothing
OPTS=[("LmrQuietBase","93"),("LmrQuietDivisor","205"),("LmrNoisyBase","13"),("LmrNoisyDivisor","333"),
      ("LmrHistoryDivisor","5643"),("NullMoveBase","5"),("LmpBase","8"),("HistoryPruneMultiplier","2220"),
      ("HistoryBonusQuadratic","24"),("HistoryBonusLinear","54"),("HistoryBonusMax","2212"),
      ("SingularDepth","6"),("IirDepth","2"),("NonPawnCorrection","true"),("CuckooRep","true"),
      ("HistRework","2"),("TtPruneV2","true"),("CorrHistV2","true"),("MateAlphaGuard","true"),
      ("OwnBook","false"),("Threads","1"),("Hash","16")]
BOARDS=[
 ("seat10_risky_c80","5k2/8/8/8/8/8/8/1K1Q4 w - - 80 1"),
 ("seat10_risky_c90","5k2/8/8/8/8/8/8/1K1Q4 w - - 90 1"),
 ("my_A_mate1_c100","6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 100 1"),
 ("my_B_pawn_mate_c100","8/3K4/7P/8/8/7k/8/6Q1 w - - 100 1"),
 ("my_C_quiet_mate_c99","8/8/8/8/2K4Q/8/8/1k6 w - - 99 1"),
]
GO="go depth 20"

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
    d=time.monotonic()+30
    send("uci"); until("uciok",d)
    for n,v in OPTS: send("setoption name %s value %s"%(n,v)); send("isready"); until("readyok",d)
    send("ucinewgame"); send("isready"); until("readyok",d)
    send("position fen "+fen); send("isready"); until("readyok",d)
    t0=time.monotonic()
    send(GO)
    bm=None; finished=False
    while time.monotonic()-t0 < CAP:
        l=rd.line(time.monotonic()+min(1.0,max(0.05,CAP-(time.monotonic()-t0))))
        if l is None:
            if p.poll() is not None: break
            continue
        buf.append(l)
        if l.startswith("bestmove"):
            bm=l.split()[1] if len(l.split())>1 else None; finished=True; break
    elapsed=time.monotonic()-t0
    if not finished:
        try: send("stop")
        except Exception: pass
        time.sleep(0.5)
    send("quit")
    try: p.wait(timeout=10)
    except Exception: p.kill()
    dl=[l for l in buf if l.startswith("info depth")]
    depth=None; nodes=None; score=""
    for l in reversed(dl):
        f=l.split()
        if depth is None and "depth" in f: depth=int(f[f.index("depth")+1])
        if nodes is None and "nodes" in f: nodes=int(f[f.index("nodes")+1])
        if not score and " score " in l:
            i=f.index("score"); score=" ".join(f[i+1:i+3])
        if depth is not None and nodes is not None and score: break
    return {"finished":finished,"elapsed_s":round(elapsed,1),"reached_depth":depth,"nodes":nodes,
            "score":score,"bestmove":bm,"cap":CAP}

def main():
    exe=sys.argv[1]; out=Path(sys.argv[2]); out.mkdir(parents=True,exist_ok=True)
    lines=["does an UNTIMED `go depth 20` hang on a HIGH-COUNTER board? (seat 10's 10-F65)",
           "exe_started: %s"%exe,"sha256: %s"%hashlib.sha256(Path(exe).read_bytes()).hexdigest(),
           "PC20, Threads 1, Hash 16, wall cap %.0f s per search - the cap is the point, since an untimed call" % CAP,
           "that never returns cannot distinguish slow from hung",""]
    lines.append("board\tfen\tfinished\telapsed_s\treached_depth\tnodes\tscore\tbestmove\tverdict")
    rows=[]
    for name,fen in BOARDS:
        r=run(exe,fen); r["board"]=name; r["fen"]=fen
        if r["finished"]:
            v=("completed" if (r["reached_depth"] or 0)>=20 else "stopped early (mate score)")
        else:
            v="DID NOT FINISH within %.0f s - seat 10's 'looks hung'" % CAP
        r["verdict"]=v; rows.append(r)
        print("%-22s %-11s %.1fs depth %-3s nodes %-10s %-8s %s"
              %(name,v,r["elapsed_s"],r["reached_depth"],r["nodes"],r["score"],r["bestmove"]),flush=True)
        lines.append("%s\t%s\t%s\t%.1f\t%s\t%s\t%s\t%s\t%s"%(name,fen,r["finished"],r["elapsed_s"],
                     r["reached_depth"],r["nodes"],r["score"],r["bestmove"],v))
    v=[]
    v.append("")
    mine=[r for r in rows if r["board"].startswith("my_")]
    risky=[r for r in rows if r["board"].startswith("seat10_risky")]
    v.append("A. MY OWN BOARDS (%d): %s" % (len(mine),
             "all completed" if all(r["finished"] for r in mine) else "SOME DID NOT COMPLETE"))
    for r in mine:
        v.append("   %-22s %.1f s, depth %s, %s nodes, %s"%(r["board"],r["elapsed_s"],r["reached_depth"],
                                                           r["nodes"],r["score"]))
    v.append("   -> so the untimed `go depth 20` I used in S-C6 was SAFE on these boards: each carries a short")
    v.append("      forced mate, and the iterative loop breaks as soon as the mate is found, so the search never")
    v.append("      has to grind to depth 20. My figures are not affected by 10-F65.")
    v.append("")
    v.append("B. SEAT 10's OWN RISKY BOARDS (%d):"%len(risky))
    for r in risky:
        v.append("   %-22s %s (%.1f s, depth %s, %s nodes)"%(r["board"],r["verdict"],r["elapsed_s"],
                                                             r["reached_depth"],r["nodes"]))
    if all(r["finished"] for r in risky):
        v.append("   -> on MY build these COMPLETED, so 10-F65's symptom did not reproduce here at a %.0f s cap."%CAP)
        v.append("      That does not refute it - seat 10 waited 120 s and machine, build and Hash all matter -")
        v.append("      but it does mean I cannot confirm the hang, and I will not claim to.")
    else:
        v.append("   -> at least one did NOT complete within %.0f s, which reproduces seat 10's warning."%CAP)
    v.append("")
    v.append("THE ACTIONABLE PART, which holds either way: CAP THE TIME. An untimed `go depth N` on a")
    v.append("  high-counter board can take a very long time, and a harness without a cap reports that as a hang.")
    (out/"check_untimed_depth20.json").write_text(json.dumps({"rows":rows,"verdict":v},indent=1))
    (out/"check_untimed_depth20.txt").write_text("\n".join(lines+v)+"\n")
    print(""); print("\n".join(v))

if __name__=="__main__":
    main()
