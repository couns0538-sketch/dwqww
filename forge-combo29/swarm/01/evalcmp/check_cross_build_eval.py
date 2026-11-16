#!/usr/bin/env python3
"""swarm seat 01: CHECK of seat 06's S-F31 — do the PC r15 build and the base build evaluate identically?

Seat 06's claim, verbatim:
  "CROSS-BUILD: the PC r15 build (PC20) and the base build (S14) give IDENTICAL hce/nnue/total for every one
   of 3,000 shared positions - 0 disagreements. So the engine the owner plays evaluates a position exactly as
   the tree the swarm builds does (with the built-in net)."

That matters for the owner: if evaluation is identical, every evaluation-based finding on the base tree
transfers to his engine, and the PC patch is search-only in effect. If it is NOT identical, a whole class of
base-tree evaluation results does not transfer.

Method: the engine's `eval` command prints hce/nnue/total. I run it on the same positions through both builds
with each build's own settings regime (base under S14, PC under PC20, since those are the regimes seat 06
names), fresh process per position, and compare the three numbers per position. I also control for the trap
seat 16's S-C5 recorded - `eval` is side-to-move relative - by comparing only identical FENs, so the sign
question cannot arise.

Usage: check_cross_build_eval.py <base-exe> <pc-exe> <outdir> [n-positions]
"""
import hashlib, json, os, re, select, subprocess, sys, time
from pathlib import Path

TIMEOUT=120.0
S14=[("LmrQuietBase","93"),("LmrQuietDivisor","205"),("LmrNoisyBase","13"),("LmrNoisyDivisor","333"),
     ("LmrHistoryDivisor","5643"),("NullMoveBase","5"),("LmpBase","8"),("HistoryPruneMultiplier","2220"),
     ("HistoryBonusQuadratic","24"),("HistoryBonusLinear","54"),("HistoryBonusMax","2212"),
     ("SingularDepth","6"),("IirDepth","2"),("NonPawnCorrection","true")]
PC20=S14+[("CuckooRep","true"),("HistRework","2"),("TtPruneV2","true"),("CorrHistV2","true"),
          ("MateAlphaGuard","true"),("OwnBook","false"),("Threads","1"),("Hash","16")]
BASE_OPTS=S14+[("Threads","1"),("Hash","16"),("OwnBook","false")]

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

def evals(exe, fen, opts):
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
    for n,v in opts:
        send("setoption name %s value %s"%(n,v)); send("isready"); until("readyok",d)
    send("isready"); until("readyok",d)
    send("position fen "+fen); send("isready"); until("readyok",d)
    send("eval")
    # eval prints an info string line; read until we see it or the deadline
    got=None
    end=time.monotonic()+10
    while time.monotonic()<end:
        l=rd.line(time.monotonic()+1.0)
        if l is None: break
        if "eval" in l and ("hce" in l or "nnue" in l or "total" in l):
            got=l; break
    send("quit")
    try: p.wait(timeout=20)
    except Exception: p.kill()
    if not got: return None
    m=re.search(r"hce\s+(-?\d+)\s+nnue\s+(-?\d+)\s+total\s+(-?\d+)", got)
    if not m: return {"raw":got}
    return {"hce":int(m.group(1)),"nnue":int(m.group(2)),"total":int(m.group(3)),"raw":got}

def main():
    base,pc,out=sys.argv[1],sys.argv[2],Path(sys.argv[3])
    n=int(sys.argv[4]) if len(sys.argv)>4 else 60
    out.mkdir(parents=True,exist_ok=True)
    fens=[]
    for line in open("/agent/repos/dwqww/forge-combo29/swarm/01/job1/set_G.epd"):
        line=line.strip()
        if not line or line.startswith("#"): continue
        parts=line.split()
        if len(parts)>=4: fens.append(" ".join(parts[:4])+" 0 1")
        if len(fens)>=n: break
    # also some random R positions, so it is not all G
    try:
        rlines=[l.strip() for l in open("/agent/repos/dwqww/forge-combo29/swarm/01/job1/set_R.fens") if l.strip()]
        fens += rlines[:n]
    except Exception: pass
    lines=["CHECK of seat 06's S-F31: do PC r15 (PC20) and base (S14) evaluate IDENTICALLY?",
           "base %s sha256 %s"%(base,hashlib.sha256(Path(base).read_bytes()).hexdigest()),
           "pc   %s sha256 %s"%(pc,hashlib.sha256(Path(pc).read_bytes()).hexdigest()),
           "regimes exactly as seat 06 names them: base under S14, PC under PC20; fresh process per position",
           "comparing IDENTICAL FENs only, so the side-to-move-relative eval trap (seat 16 S-C5) cannot arise",
           "positions: %d (%d from set_G, %d from set_R)"%(len(fens),min(n,len(fens)),max(0,len(fens)-n)),""]
    lines.append("idx\thce_base\tnnue_base\ttotal_base\thce_pc\tnnue_pc\ttotal_pc\tidentical")
    same=0; diff=0; missing=0; diffs=[]
    for i,fen in enumerate(fens):
        a=evals(base,fen,BASE_OPTS); b=evals(pc,fen,PC20)
        if not a or not b or "hce" not in a or "hce" not in b:
            missing+=1
            lines.append("%d\t- missing -"%i); continue
        ident=(a["hce"],a["nnue"],a["total"])==(b["hce"],b["nnue"],b["total"])
        if ident: same+=1
        else:
            diff+=1; diffs.append({"idx":i,"fen":fen,"base":a,"pc":b})
        lines.append("%d\t%d\t%d\t%d\t%d\t%d\t%d\t%s"%(i,a["hce"],a["nnue"],a["total"],
                     b["hce"],b["nnue"],b["total"],ident))
        if i<5 or not ident:
            print("%-3d base %5d/%5d/%5d | pc %5d/%5d/%5d | %s"%(i,a["hce"],a["nnue"],a["total"],
                  b["hce"],b["nnue"],b["total"],"IDENTICAL" if ident else "DIFFERS"),flush=True)
    v=[]
    v.append("")
    v.append("RESULT: %d identical, %d differing, %d unreadable, over %d positions."%(same,diff,missing,len(fens)))
    if diff==0 and same>0:
        v.append("VERDICT: CONFIRMS seat 06's S-F31. The PC build and the base build evaluate a position")
        v.append("  identically, so every evaluation-based result on the base tree transfers to the engine the")
        v.append("  owner plays, and the PC patch's effect is SEARCH only, not evaluation.")
    elif diff>0:
        v.append("VERDICT: does NOT fully confirm - %d of %d positions differ. First five differences:"%(
            diff,same+diff))
        for d in diffs[:5]:
            v.append("  idx %d: base %s vs pc %s"%(d["idx"],d["base"],d["pc"]))
        v.append("  So an evaluation-based base-tree result may NOT transfer, and the scope needs stating.")
    else:
        v.append("VERDICT: INCONCLUSIVE - no position produced a readable eval line, so nothing was compared.")
    (out/"check_cross_build_eval.json").write_text(json.dumps(
        {"same":same,"diff":diff,"missing":missing,"diffs":diffs,"verdict":v},indent=1))
    (out/"check_cross_build_eval.txt").write_text("\n".join(lines+v)+"\n")
    print(""); print("\n".join(v))

if __name__=="__main__":
    main()
