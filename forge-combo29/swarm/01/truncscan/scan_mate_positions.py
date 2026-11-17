#!/usr/bin/env python3
"""swarm seat 01: the truncation RATE, measured on positions that actually HAVE forced mates.

The first scan (40 positions of set_G at 20,000 / 50,000 / 250,000 nodes) found **0 mate scores in 120 cells**.
That is itself a finding: the defect cannot show up on positions where no mate exists, so set_G is the wrong
population for measuring its rate — it is the right population for saying the defect is rare in ordinary play.

To measure the rate where it CAN occur, I need positions with a forced mate available. This builds that
population from the engine itself: take the set_G board with the mate at 50,000 nodes (the known violator) and
the other known mate boards, plus short forced mates found by scanning for `mate N` scores, then run each at the
three match budgets and replay every mate PV.

Two questions, deliberately separated:
  RATE ON MATE POSITIONS  - among positions where a mate is found, how many claim a mate their PV cannot fill?
  RATE IN ORDINARY PLAY   - from the first scan: 0 of 120 set_G cells carried a mate score at all, so the
                            defect cannot bite there; that is reported as its own result.

Usage: scan_mate_positions.py <pc-exe> <outdir>
"""
import hashlib, json, os, re, select, subprocess, sys, time
from pathlib import Path
import chess

TIMEOUT=180.0
OPTS=[("LmrQuietBase","93"),("LmrQuietDivisor","205"),("LmrNoisyBase","13"),("LmrNoisyDivisor","333"),
      ("LmrHistoryDivisor","5643"),("NullMoveBase","5"),("LmpBase","8"),("HistoryPruneMultiplier","2220"),
      ("HistoryBonusQuadratic","24"),("HistoryBonusLinear","54"),("HistoryBonusMax","2212"),
      ("SingularDepth","6"),("IirDepth","2"),("NonPawnCorrection","true"),("CuckooRep","true"),
      ("HistRework","2"),("TtPruneV2","true"),("CorrHistV2","true"),("MateAlphaGuard","true"),
      ("OwnBook","false"),("Threads","1"),("Hash","16")]
BUDGETS=[20000,50000,250000]
MATE_POSITIONS=[
 ("known_violator","r2r4/pB2kpp1/n1p4p/1p5p/2n5/1q1bP2P/2PBN3/4K2R b - - 1 40"),
 ("G192_pawn_endgame","8/8/1p6/8/p3p3/8/2Kpk3/8 w - - 0 1"),
 ("KR_mate","6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 0 1"),
 ("KQ_mate3","8/8/8/8/2K4Q/8/8/1k6 w - - 0 1"),
 ("pawn_reset_mate","8/3K4/7P/8/8/7k/8/6Q1 w - - 100 1"),
 ("KQK_win","8/5K2/7Q/4k3/8/8/8/8 w - - 0 1"),
]

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
    d=time.monotonic()+60
    send("uci"); until("uciok",d)
    for n,v in OPTS: send("setoption name %s value %s"%(n,v)); send("isready"); until("readyok",d)
    send("ucinewgame"); send("isready"); until("readyok",d)
    send("position fen "+fen); send("isready"); until("readyok",d)
    send("go nodes %d"%budget)
    dl=[]
    while True:
        l=rd.line(time.monotonic()+TIMEOUT)
        if l is None: break
        if l.startswith("info depth"): dl.append(l)
        if l.startswith("bestmove"): break
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
    return {"score":score,"depth":depth,"pv":pv,"pv_plies":len(pv)}

def mate_n(s):
    m=re.match(r"mate (-?\d+)$", s.strip())
    return int(m.group(1)) if m else None

def replay(fen,pv):
    b=chess.Board(fen)
    for i,u in enumerate(pv):
        try: mv=chess.Move.from_uci(u)
        except ValueError: return False,"unparsable"
        if mv not in b.legal_moves: return False,"illegal"
        b.push(mv)
        if b.is_checkmate(): return True,"mate at ply %d"%(i+1)
    return False,"ended without mate"

def main():
    exe=sys.argv[1]; out=Path(sys.argv[2]); out.mkdir(parents=True,exist_ok=True)
    lines=["the truncation RATE on positions that actually have forced mates (set_G has almost none at these budgets)",
           "exe_started: %s"%exe,"sha256: %s"%hashlib.sha256(Path(exe).read_bytes()).hexdigest(),
           "PC20, Threads 1, Hash 16, OwnBook false, fresh process per cell",""]
    lines.append("position\tbudget\tscore\tpv_plies\tneeded\tpv_mates\tverdict")
    rows=[]
    for name,fen in MATE_POSITIONS:
        for b in BUDGETS:
            r=run(exe,fen,b); n=mate_n(r["score"])
            if n is None:
                rows.append({"pos":name,"budget":b,**r,"mate_n":None,"truncated":False})
                print("%-20s %-7d %-9s no mate score"%(name,b,r["score"]),flush=True)
                lines.append("%s\t%d\t%s\t-\t-\t-\tno mate score"%(name,b,r["score"]))
                continue
            needed=(2*abs(n)-1) if n>0 else 2*abs(n)
            mates,note=replay(fen,r["pv"])
            trunc=not mates
            rows.append({"pos":name,"budget":b,**r,"mate_n":n,"needed":needed,
                         "pv_mates":mates,"note":note,"truncated":trunc})
            print("%-20s %-7d %-9s pv %-2d need %-3d mates=%-5s %s"
                  %(name,b,r["score"],r["pv_plies"],needed,mates,"TRUNCATED" if trunc else "ok"),flush=True)
            lines.append("%s\t%d\t%s\t%d\t%d\t%s\t%s"%(name,b,r["score"],r["pv_plies"],needed,mates,
                         "TRUNCATED" if trunc else "ok"))
    mate_cells=[r for r in rows if r.get("mate_n") is not None]
    trunc=[r for r in mate_cells if r["truncated"]]
    v=[]
    v.append("")
    v.append("Mate scores found: %d of %d cells. TRUNCATED: %d of %d mate cells (%.0f %%)."
             %(len(mate_cells),len(rows),len(trunc),len(mate_cells),
               100.0*len(trunc)/len(mate_cells) if mate_cells else 0))
    if trunc:
        v.append("Truncated cells:")
        for t in trunc:
            v.append("  %s at budget %d: %s, pv %d of %d needed"%(t["pos"],t["budget"],t["score"],t["pv_plies"],t["needed"]))
    v.append("")
    v.append("THE TWO RATES, separated because they answer different questions:")
    v.append("  ON MATE POSITIONS: %d of %d mate cells truncated (%.0f %%) - this is the defect's incidence where"
             %(len(trunc),len(mate_cells),100.0*len(trunc)/len(mate_cells) if mate_cells else 0))
    v.append("    it can occur at all.")
    v.append("  IN ORDINARY PLAY: 0 of 120 set_G cells carried ANY mate score at these three budgets, so the")
    v.append("    defect has no opportunity there. That is a statement about set_G at 20k/50k/250k, not a claim")
    v.append("    that it is harmless everywhere: an endgame with a forced mate is where it lives.")
    (out/"scan_mate_positions.json").write_text(json.dumps({"rows":rows,"verdict":v},indent=1))
    (out/"scan_mate_positions.txt").write_text("\n".join(lines+v)+"\n")
    print(""); print("\n".join(v))

if __name__=="__main__":
    main()
