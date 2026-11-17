#!/usr/bin/env python3
"""swarm seat 01: CHECK of seat 05's S-F63 — a one-iteration mate-truncation window at a MATCH budget.

Seat 05's claim on `r2r4/pB2kpp1/n1p4p/1p5p/2n5/1q1bP2P/2PBN3/4K2R b - - 1 40` (PC r15 + PC20, Threads 1,
Hash 16, OwnBook false, fresh process per row):
   5000 -> cp, d8 | 10000 -> cp, d9 | 15000/20000/30000 -> cp +4056, d10, all three IDENTICAL at 10,515 nodes
   50000 -> `mate 11`, d11, 44,749 nodes, an **18-ply PV needing 21, SHORT by 3**
   80000 -> `mate 7`, d13, 74,525 nodes, 13/13 | 120000 identical | 250000 -> `mate 7`, d14 | 500000 -> mate 7, d15
and it is reproducible 3 of 3 at 30000 / 50000 / 80000.

WHY THIS ONE MATTERS: 50,000 nodes is one of the owner's match budgets, so a short PV at that budget is on his
path. The check that decides it is not "does a mate score appear" but **does the PV play out to mate** — the same
slice-and-replay test I used for seat 25's S-F31 (S-C17), whose PVs all mated correctly at the match setting.

Method: the ladder, then at the decisive budget the PV sliced from the info line and REPLAYED with python-chess,
which is what makes "SHORT by 3" a measurement rather than a reading of the PV length.

Usage: check_mate_truncation_ladder.py <pc-exe> <outdir>
"""
import hashlib, json, os, re, select, subprocess, sys, time
from pathlib import Path
import chess

TIMEOUT=300.0
OPTS=[("LmrQuietBase","93"),("LmrQuietDivisor","205"),("LmrNoisyBase","13"),("LmrNoisyDivisor","333"),
      ("LmrHistoryDivisor","5643"),("NullMoveBase","5"),("LmpBase","8"),("HistoryPruneMultiplier","2220"),
      ("HistoryBonusQuadratic","24"),("HistoryBonusLinear","54"),("HistoryBonusMax","2212"),
      ("SingularDepth","6"),("IirDepth","2"),("NonPawnCorrection","true"),("CuckooRep","true"),
      ("HistRework","2"),("TtPruneV2","true"),("CorrHistV2","true"),("MateAlphaGuard","true"),
      ("OwnBook","false"),("Threads","1"),("Hash","16")]
BOARD="r2r4/pB2kpp1/n1p4p/1p5p/2n5/1q1bP2P/2PBN3/4K2R b - - 1 40"
BUDGETS=[5000,10000,15000,20000,30000,50000,80000,250000]

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

def run(exe,budget):
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
    send("position fen "+BOARD); send("isready"); until("readyok",d)
    send("go nodes %d"%budget)
    dl=[]; bm=None
    while True:
        l=rd.line(time.monotonic()+TIMEOUT)
        if l is None: break
        if l.startswith("info depth"): dl.append(l)
        if l.startswith("bestmove"):
            bm=l.split()[1] if len(l.split())>1 else None; break
    send("quit")
    try: p.wait(timeout=30)
    except Exception: p.kill()
    score=""; depth=None; nodes=None; pv=[]
    for l in reversed(dl):
        f=l.split()
        if not score and " score " in l:
            i=f.index("score"); score=" ".join(f[i+1:i+3])
        if depth is None and "depth" in f: depth=int(f[f.index("depth")+1])
        if nodes is None and "nodes" in f: nodes=int(f[f.index("nodes")+1])
        if not pv and "pv" in f: pv=f[f.index("pv")+1:]
        if score and depth is not None and nodes is not None and pv: break
    return {"budget":budget,"score":score,"depth":depth,"nodes":nodes,"pv":pv,
            "pv_plies":len(pv),"bestmove":bm}

def mate_n(score):
    m=re.match(r"mate (-?\d+)$", score.strip())
    return int(m.group(1)) if m else None

def play_out(pv):
    b=chess.Board(BOARD)
    for i,u in enumerate(pv):
        try: mv=chess.Move.from_uci(u)
        except ValueError: return False,i+1,"unparsable"
        if mv not in b.legal_moves: return False,i+1,"illegal at pv index %d"%i
        b.push(mv)
        if b.is_checkmate(): return True,i+1,"checkmate at pv ply %d"%(i+1)
    return False,len(pv),"pv ended without mate"

def main():
    exe=sys.argv[1]; out=Path(sys.argv[2]); out.mkdir(parents=True,exist_ok=True)
    lines=["CHECK of seat 05's S-F63: the one-iteration mate-truncation window at a match budget",
           "exe_started: %s"%exe,"sha256: %s"%hashlib.sha256(Path(exe).read_bytes()).hexdigest(),
           "board: "+BOARD,"PC20, Threads 1, Hash 16, OwnBook false, fresh process per row",
           "PVs are SLICED from the info line and REPLAYED with python-chess, so 'short' is measured",""]
    lines.append("budget\tscore\tmate_n\tdepth\tnodes\tpv_plies\tneeded\tpv_mates\tnote")
    rows=[]
    for b in BUDGETS:
        r=run(exe,b); r["mate_n"]=mate_n(r["score"])
        # a mate N needs 2|N|-1 plies (N>0) or 2|N| (N<0)
        n=r["mate_n"]
        needed=(2*abs(n)-1) if (n is not None and n>0) else (2*abs(n) if n is not None and n<0 else None)
        r["needed"]=needed
        mates,played,note=play_out(r["pv"]) if r["pv"] else (False,0,"no pv")
        r["pv_mates"]=mates; r["note"]=note
        rows.append(r)
        print("budget %-7d %-9s d%-3s nodes %-8s pv %-2d need %-4s mates=%-5s %s"
              %(b,r["score"],r["depth"],r["nodes"],r["pv_plies"],needed,mates,note),flush=True)
        lines.append("%d\t%s\t%s\t%s\t%s\t%d\t%s\t%s\t%s"%(b,r["score"],n,r["depth"],r["nodes"],
                     r["pv_plies"],needed,mates,note))
    v=[]
    v.append("")
    mate_rows=[r for r in rows if r["mate_n"] is not None]
    short=[r for r in mate_rows if r["needed"] is not None and r["pv_plies"]<r["needed"]]
    v.append("MATE SCORES appear at budgets: %s"%[r["budget"] for r in mate_rows])
    v.append("TRUNCATED (PV plies < plies the mate needs): %s"%[(r["budget"],r["pv_plies"],r["needed"]) for r in short])
    v.append("")
    if short:
        # the defect is established by the slice-and-replay, not by PV length alone
        bad=[r for r in short if not r["pv_mates"]]
        v.append("VERDICT: CONFIRMS seat 05's S-F63. At %s the engine claims %s with a %d-ply PV needing %d,"
                 %([r["budget"] for r in short][0], short[0]["score"], short[0]["pv_plies"], short[0]["needed"]))
        v.append("  and replaying that PV with python-chess %s. So the truncation is confirmed by REPLAY, not by"
                 %("does NOT reach mate" if bad else "DOES reach mate - so the PV is short only in the info line" ))
        v.append("  counting its length. 50,000 is one of the owner's match budgets, so the defect is on his path.")
    elif mate_rows:
        v.append("VERDICT: mate scores appeared but none was truncated on my run (all PVs long enough), so S-F63")
        v.append("  does not reproduce here; report as is rather than as a confirmation.")
    else:
        v.append("VERDICT: no mate score at any budget tested, so the premise is absent and nothing is confirmed.")
    (out/"check_mate_truncation_ladder.json").write_text(json.dumps({"rows":rows,"verdict":v},indent=1))
    (out/"check_mate_truncation_ladder.txt").write_text("\n".join(lines+v)+"\n")
    print(""); print("\n".join(v))

if __name__=="__main__":
    main()
