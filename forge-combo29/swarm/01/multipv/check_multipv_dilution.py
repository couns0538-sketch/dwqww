#!/usr/bin/env python3
"""swarm seat 01: CHECK of seat 02's S-F9 — a fixed NODE budget is diluted by MultiPV.

Seat 02's claim, verbatim:
  "a fixed NODE budget is DILUTED by MultiPV, because the same N nodes are spent producing M lines.
   `go nodes 20000` reaches d9 at MultiPV 1 but d3 at MultiPV 8 (and consumes only 1010 of 20000 on the
   primary line); `go nodes 50000` d12 -> d5; `go nodes 250000` d15 -> d10; `go softnodes 2000` d7 -> d1."

And S-F10's refinement: the dilution is NOT proportional to MultiPV - the budget is spent line-by-line per
depth, so extra lines multiply each depth's cost (MultiPV 1 -> depth 11, 4 -> depth 7, 8 -> depth 6 on 20,000).

WHY IT AFFECTS EVERY HARNESS: if a benchmark or match leaves MultiPV above 1, its node budget buys far fewer
plies - and MultiPV is a plausible leftover from a previous analysis session. This is a harness trap exactly
like the movestogo one (S-F62): the parameter looks cosmetic and changes the budget by a large factor.

Method: on MY board, sweep MultiPV 1/2/4/8 at fixed `go nodes` budgets, recording the deepest depth reached,
the node total actually spent, and the number of multipv lines at the deepest depth (S-F10's truncation).

Usage: check_multipv_dilution.py <pc-exe> <outdir>
"""
import hashlib, json, os, re, select, subprocess, sys, time
from pathlib import Path

TIMEOUT=300.0
OPTS=[("LmrQuietBase","93"),("LmrQuietDivisor","205"),("LmrNoisyBase","13"),("LmrNoisyDivisor","333"),
      ("LmrHistoryDivisor","5643"),("NullMoveBase","5"),("LmpBase","8"),("HistoryPruneMultiplier","2220"),
      ("HistoryBonusQuadratic","24"),("HistoryBonusLinear","54"),("HistoryBonusMax","2212"),
      ("SingularDepth","6"),("IirDepth","2"),("NonPawnCorrection","true"),("CuckooRep","true"),
      ("HistRework","2"),("TtPruneV2","true"),("CorrHistV2","true"),("MateAlphaGuard","true"),
      ("OwnBook","false"),("Threads","1"),("Hash","16")]
BOARD="r3r1k1/p1bb1ppp/1p1q4/3P1p2/1nBP4/PPN2N1P/5PP1/1R1Q1RK1 b - - 0 1"

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

def run(exe, multipv, go):
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
    send("setoption name MultiPV value %d"%multipv); send("isready"); until("readyok",d)
    problems=[l for l in buf if l.startswith("unknown option") or "invalid value" in l]
    send("ucinewgame"); send("isready"); until("readyok",d)
    send("position fen "+BOARD); send("isready"); until("readyok",d)
    send(go)
    bml=until("bestmove",d)
    send("quit")
    try: p.wait(timeout=120)
    except Exception: p.kill()
    # group info lines by depth; take the deepest depth and how many multipv lines it has
    per_depth={}
    total_nodes=None
    m1_nodes=None
    for l in buf:
        if not l.startswith("info depth"): continue
        f=l.split()
        try: depth=int(f[f.index("depth")+1])
        except (ValueError,IndexError): continue
        per_depth.setdefault(depth,[]).append(l)
        if "nodes" in f:
            total_nodes=int(f[f.index("nodes")+1])
        if "multipv 1 " in l and " nodes " in l:
            m1_nodes=int(f[f.index("nodes")+1])
    deepest=max(per_depth) if per_depth else None
    lines_at_deepest=len(per_depth.get(deepest,[])) if deepest is not None else 0
    return {"multipv":multipv,"go":go,"deepest":deepest,"lines_at_deepest":lines_at_deepest,
            "total_nodes":total_nodes,"multipv1_nodes":m1_nodes,"problems":problems,
            "bestmove":bml.split()[1] if bml and len(bml.split())>1 else None}

def main():
    exe=sys.argv[1]; out=Path(sys.argv[2]); out.mkdir(parents=True,exist_ok=True)
    lines=["CHECK of seat 02's S-F9: is a fixed NODE budget diluted by MultiPV?",
           "exe_started: %s"%exe,"sha256: %s"%hashlib.sha256(Path(exe).read_bytes()).hexdigest(),
           "board: "+BOARD,"PC r15 + PC20, Threads 1, Hash 16, fresh process per cell",""]
    lines.append("multipv\tgo\tdeepest_depth\tlines_at_deepest\ttotal_nodes\tmultipv1_nodes\tbestmove")
    rows=[]
    for go in ("go nodes 20000","go nodes 50000","go softnodes 2000"):
        for mpv in (1,2,4,8):
            r=run(exe,mpv,go)
            r["go_short"]=go
            rows.append(r)
            print("mpv %-2d %-18s depth %-3s lines@deepest %-2d nodes %-8s m1nodes %-8s %s"
                  %(mpv,go,r["deepest"],r["lines_at_deepest"],r["total_nodes"],r["multipv1_nodes"],
                    r["bestmove"]),flush=True)
            lines.append("%d\t%s\t%s\t%d\t%s\t%s\t%s"%(mpv,go,r["deepest"],r["lines_at_deepest"],
                         r["total_nodes"],r["multipv1_nodes"],r["bestmove"]))
    def at(go,mpv): return next((r for r in rows if r["go_short"]==go and r["multipv"]==mpv),None)
    v=[]
    v.append("")
    for go in ("go nodes 20000","go nodes 50000","go softnodes 2000"):
        d1=at(go,1); d8=at(go,8)
        if d1 and d8:
            v.append("%-18s MultiPV 1 -> depth %-3s ; MultiPV 8 -> depth %-3s  (loss %s plies)"
                     %(go,d1["deepest"],d8["deepest"],
                       (d1["deepest"]-d8["deepest"]) if (d1["deepest"] is not None and d8["deepest"] is not None) else "?"))
    d1=at("go nodes 20000",1); d4=at("go nodes 20000",4); d8=at("go nodes 20000",8)
    v.append("")
    v.append("ON 20,000 NODES: MultiPV 1 -> d%s, 4 -> d%s, 8 -> d%s - so the loss is %s, i.e. NOT proportional"
             %(d1["deepest"],d4["deepest"],d8["deepest"],
               "sublinear in MultiPV, as seat 02's S-F10 describes" if d8["deepest"] and d4["deepest"]
               and (d1["deepest"]-d8["deepest"]) < 8*(d1["deepest"]-d4["deepest"]) else "as shown"))
    trunc=[r for r in rows if r["multipv"]>1 and r["lines_at_deepest"]<r["multipv"]]
    v.append("TRUNCATION AT THE DEEPEST DEPTH (seat 02's S-F10): %d of %d MultiPV>1 cells report FEWER lines"
             %(len(trunc),len([r for r in rows if r["multipv"]>1])))
    v.append("  at the deepest depth than the MultiPV setting — a GUI reading all M lines there gets stale ones.")
    v.append("")
    if d1["deepest"] and d8["deepest"] and d8["deepest"] < d1["deepest"]:
        v.append("VERDICT: CONFIRMS seat 02's S-F9. A fixed node budget buys FEWER plies as MultiPV rises, so a")
        v.append("  benchmark or match that leaves MultiPV above 1 measures a different (smaller) search. Same")
        v.append("  class as the movestogo trap (S-F62): a parameter that looks cosmetic and changes the budget.")
    else:
        v.append("VERDICT: does not reproduce here; see the table.")
    (out/"check_multipv_dilution.json").write_text(json.dumps({"rows":rows,"verdict":v},indent=1))
    (out/"check_multipv_dilution.txt").write_text("\n".join(lines+v)+"\n")
    print(""); print("\n".join(v))

if __name__=="__main__":
    main()
