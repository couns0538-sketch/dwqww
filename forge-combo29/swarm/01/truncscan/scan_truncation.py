#!/usr/bin/env python3
"""swarm seat 01: HOW WIDESPREAD is the mate-PV truncation at the owner's three match budgets?

Seat 05's S-F63/S-F64 found the defect on specific positions at specific budgets, and I confirmed one case
exactly by replay (S-C29). The question the owner actually needs answered is not "does it happen" but "how often,
at the budgets I use". That is a scan, and it is only possible because I now have a test that is proven able to
both find and clear the defect (the 50,000 case fails, 80,000 and 250,000 pass).

Scan: every position in set_G (353) at the owner's three match budgets — 20,000 / 50,000 / 250,000 nodes —
PC20, Threads 1, Hash 16, fresh process per cell. For each cell with a mate score, slice the PV and replay it;
count truncated (mate claimed, PV does not mate).

Reporting: how many cells carry a mate score at all, how many of those are truncated, and which budgets and
positions they fall on. A truncation rate per budget is the number the owner can act on.

Time-bounded: 353 positions x 3 budgets is 1059 searches. To keep each command inside the limit this script
takes a --shard argument and appends to a results file, so it can be run in several pieces.

Usage: scan_truncation.py <pc-exe> <outdir> [--limit N] [--offset K]
"""
import hashlib, json, os, re, select, subprocess, sys, time
from pathlib import Path
import chess

TIMEOUT=120.0
OPTS=[("LmrQuietBase","93"),("LmrQuietDivisor","205"),("LmrNoisyBase","13"),("LmrNoisyDivisor","333"),
      ("LmrHistoryDivisor","5643"),("NullMoveBase","5"),("LmpBase","8"),("HistoryPruneMultiplier","2220"),
      ("HistoryBonusQuadratic","24"),("HistoryBonusLinear","54"),("HistoryBonusMax","2212"),
      ("SingularDepth","6"),("IirDepth","2"),("NonPawnCorrection","true"),("CuckooRep","true"),
      ("HistRework","2"),("TtPruneV2","true"),("CorrHistV2","true"),("MateAlphaGuard","true"),
      ("OwnBook","false"),("Threads","1"),("Hash","16")]
BUDGETS=[20000,50000,250000]

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

def run(exe,fen,budget):
    p=subprocess.Popen([exe],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,bufsize=0,cwd="/tmp")
    rd=R(p.stdout.fileno())
    def until(pre,dl):
        while True:
            l=rd.line(dl)
            if l is None: return None
            if l.startswith(pre): return l
    def send(s): p.stdin.write((s+"\n").encode()); p.stdin.flush()
    d=time.monotonic()+40
    send("uci"); until("uciok",d)
    for n,v in OPTS: send("setoption name %s value %s"%(n,v)); send("isready"); until("readyok",d)
    send("ucinewgame"); send("isready"); until("readyok",d)
    send("position fen "+fen); send("isready"); until("readyok",d)
    send("go nodes %d"%budget)
    dl=[]; bm=None
    while True:
        l=rd.line(time.monotonic()+TIMEOUT)
        if l is None: break
        if l.startswith("info depth"): dl.append(l)
        if l.startswith("bestmove"):
            bm=l.split()[1] if len(l.split())>1 else None; break
    send("quit")
    try: p.wait(timeout=20)
    except Exception: p.kill()
    score=""; depth=None; pv=[]
    for l in reversed(dl):
        f=l.split()
        if not score and " score " in l:
            i=f.index("score"); score=" ".join(f[i+1:i+3])
        if depth is None and "depth" in f: depth=int(f[f.index("depth")+1])
        if not pv and "pv" in f: pv=f[f.index("pv")+1:]
        if score and depth is not None and pv: break
    return {"score":score,"depth":depth,"pv":pv,"pv_plies":len(pv),"bestmove":bm}

def mate_n(score):
    m=re.match(r"mate (-?\d+)$", score.strip())
    return int(m.group(1)) if m else None

def replay(fen,pv):
    b=chess.Board(fen)
    for i,u in enumerate(pv):
        try: mv=chess.Move.from_uci(u)
        except ValueError: return False,"unparsable at %d"%i
        if mv not in b.legal_moves: return False,"illegal at %d"%i
        b.push(mv)
        if b.is_checkmate(): return True,"mate at ply %d"%(i+1)
    return False,"ended without mate"

def main():
    exe=sys.argv[1]; out=Path(sys.argv[2]); out.mkdir(parents=True,exist_ok=True)
    limit=int(sys.argv[sys.argv.index("--limit")+1]) if "--limit" in sys.argv else 40
    offset=int(sys.argv[sys.argv.index("--offset")+1]) if "--offset" in sys.argv else 0
    fens=[]
    for line in open("/agent/repos/dwqww/forge-combo29/swarm/01/job1/set_G.epd"):
        line=line.strip()
        if not line or line.startswith("#"): continue
        parts=line.split()
        if len(parts)>=4: fens.append(" ".join(parts[:4])+" 0 1")
    chunk=fens[offset:offset+limit]
    resfile=out/"scan.jsonl"
    done=[]
    for idx,fen in enumerate(chunk):
        gi=offset+idx
        for budget in BUDGETS:
            r=run(exe,fen,budget); n=mate_n(r["score"])
            rec={"g_index":gi,"fen":fen,"budget":budget,"score":r["score"],"mate_n":n,
                 "depth":r["depth"],"pv_plies":r["pv_plies"],"bestmove":r["bestmove"]}
            if n is not None:
                needed=(2*abs(n)-1) if n>0 else 2*abs(n)
                rec["needed"]=needed
                mates,note=replay(fen,r["pv"])
                rec["pv_mates"]=mates; rec["note"]=note
                rec["truncated"]= (not mates)
            else:
                rec["truncated"]=False
            done.append(rec)
        print("g%-3d done (%d cells mate, %d truncated so far)"
              %(gi+1,sum(1 for d in done if d["mate_n"] is not None),
                sum(1 for d in done if d.get("truncated"))),flush=True)
    with open(resfile,"a") as fh:
        for d in done: fh.write(json.dumps(d)+"\n")
    mates=[d for d in done if d["mate_n"] is not None]
    trunc=[d for d in mates if d.get("truncated")]
    print("")
    print("SHARD: positions %d..%d, %d cells, %d with a mate score, %d TRUNCATED"
          %(offset+1,offset+len(chunk),len(done),len(mates),len(trunc)))
    for t in trunc:
        print("  TRUNCATED g%d budget %d: %s, pv %d of %d needed, %s"
              %(t["g_index"]+1,t["budget"],t["score"],t["pv_plies"],t["needed"],t["note"]))
    pathlib=Path
    (out/("shard_%d_%d.txt"%(offset,offset+len(chunk)))).write_text(
        "positions %d..%d: %d cells, %d mate scores, %d truncated\n"%(offset+1,offset+len(chunk),len(done),len(mates),len(trunc)))

if __name__=="__main__":
    main()
