#!/usr/bin/env python3
"""swarm seat 01: CHECK of seat 13's S-F21 and S-F22 — the clock plateau is general, and an identical
node count means an identical move.

Seat 13's claims, verbatim:
  S-F21: "across five positions (middlegame, tactical, startpos, rook endgame, queen endgame), 11 clock values
          from 1 s to 60 s give only 6-8 DISTINCT node counts each ... Step points differ per position ... so
          this is an allocator property, not a coincidence. Repeatable to the identical node count."
  S-F22: "Across all 240 pairwise comparisons, IDENTICAL node counts ALWAYS gave an IDENTICAL move — 6 of 6,
          zero exceptions — so a quantisation plateau is literally the same search, not merely the same volume
          of work."

Both are falsifiable and both matter to my own S-C15/S-F64 clock rule: if plateaus are general, the "sweep to
find a plateau" rule applies to every position; and if identical nodes imply an identical move, then a node
count is a sufficient identifier for a search result, which is a stronger statement than I have made.

Design: five positions of DIFFERENT character, a clock ladder from 1 s to 12 s (fewer than seat 13's 11 values
but enough to show plateaus), one fresh process per cell. For each position report the number of DISTINCT
(depth, nodes) outcomes and the distinct (nodes) outcomes; then across all rows, group by node count and check
whether every group has a single bestmove.

Usage: check_plateau_general.py <pc-exe> <outdir>
"""
import hashlib, json, os, select, subprocess, sys, time
from pathlib import Path
from collections import defaultdict

TIMEOUT=300.0
OPTS=[("LmrQuietBase","93"),("LmrQuietDivisor","205"),("LmrNoisyBase","13"),("LmrNoisyDivisor","333"),
      ("LmrHistoryDivisor","5643"),("NullMoveBase","5"),("LmpBase","8"),("HistoryPruneMultiplier","2220"),
      ("HistoryBonusQuadratic","24"),("HistoryBonusLinear","54"),("HistoryBonusMax","2212"),
      ("SingularDepth","6"),("IirDepth","2"),("NonPawnCorrection","true"),("CuckooRep","true"),
      ("HistRework","2"),("TtPruneV2","true"),("CorrHistV2","true"),("MateAlphaGuard","true"),
      ("OwnBook","false"),("Threads","1"),("Hash","16")]
POSITIONS=[
 ("startpos","rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"),
 ("middlegame","1r6/2k2pp1/2p2n2/2Pppb1p/7P/1P2PPP1/P3BK2/R1R5 b - - 0 1"),
 ("tactical","r3r1k1/p1bb1ppp/1p1q4/3P1p2/1nBP4/PPN2N1P/5PP1/1R1Q1RK1 b - - 0 1"),
 ("rook_endgame","8/8/8/4k3/8/8/4K3/R7 w - - 0 1"),
 ("queen_endgame","8/5K2/7Q/4k3/8/8/8/8 w - - 0 1"),
]
CLOCKS=[1000,1500,2000,3000,4000,6000,8000,12000]

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

def run(exe,fen,clock):
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
    send("go wtime %d btime %d winc 60 binc 60"%(clock,clock))
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
    depth=None; nodes=None
    for l in reversed(dl):
        f=l.split()
        if depth is None and "depth" in f: depth=int(f[f.index("depth")+1])
        if nodes is None and "nodes" in f: nodes=int(f[f.index("nodes")+1])
        if depth is not None and nodes is not None: break
    return {"clock":clock,"depth":depth,"nodes":nodes,"bestmove":bm}

def main():
    exe=sys.argv[1]; out=Path(sys.argv[2]); out.mkdir(parents=True,exist_ok=True)
    lines=["CHECK of seat 13's S-F21 (plateau is general) and S-F22 (identical nodes ⇒ identical move)",
           "exe_started: %s"%exe,"sha256: %s"%hashlib.sha256(Path(exe).read_bytes()).hexdigest(),
           "PC20, Threads 1, Hash 16, winc=binc=60, fresh process per cell",
           "clocks: %s"%CLOCKS,""]
    allrows=[]
    summary=[]
    for name,fen in POSITIONS:
        rows=[run(exe,fen,c) for c in CLOCKS]
        for r in rows: r["position"]=name
        allrows.extend(rows)
        distinct_dn={(r["depth"],r["nodes"]) for r in rows}
        distinct_n={r["nodes"] for r in rows}
        summary.append({"position":name,"cells":len(rows),"distinct_depth_nodes":len(distinct_dn),
                        "distinct_nodes":len(distinct_n),"rows":rows})
        print("%-14s %d cells -> %d distinct (depth,nodes), %d distinct node counts"
              %(name,len(rows),len(distinct_dn),len(distinct_n)),flush=True)
        lines.append("%s: %d cells -> %d distinct (depth,nodes), %d distinct nodes"
                     %(name,len(rows),len(distinct_dn),len(distinct_n)))
        for r in rows:
            lines.append("   clock %-5d depth %-3s nodes %-8s %s"%(r["clock"],r["depth"],r["nodes"],r["bestmove"]))
    # S-F22 test: group all rows by node count; does each group have exactly one bestmove?
    by_nodes=defaultdict(set)
    for r in allrows:
        if r["nodes"] is not None: by_nodes[r["nodes"]].add(r["bestmove"])
    multi=[(n,bms) for n,bms in by_nodes.items() if len(bms)>1]
    pairs=0; same_nodes=0; same_nodes_same_move=0
    for i in range(len(allrows)):
        for j in range(i+1,len(allrows)):
            a,b=allrows[i],allrows[j]
            if a["nodes"] is None or b["nodes"] is None: continue
            pairs+=1
            if a["nodes"]==b["nodes"]:
                same_nodes+=1
                if a["bestmove"]==b["bestmove"]: same_nodes_same_move+=1
    v=[]
    v.append("")
    v.append("S-F21 (plateau is general): distinct node counts per position = %s out of %d clock values."
             %([s["distinct_nodes"] for s in summary],len(CLOCKS)))
    general=all(s["distinct_nodes"]<len(CLOCKS) for s in summary)
    v.append("  -> %s" % ("GENERAL: every position plateaus (fewer distinct outcomes than clocks)" if general
                          else "NOT uniform across positions; see the per-position counts"))
    v.append("")
    v.append("S-F22 (identical nodes ⇒ identical move): %d of the %d pairwise comparisons had equal node counts,"
             %(same_nodes,pairs))
    v.append("  and %d of those %d had the same bestmove. Groups with more than one distinct move: %d."
             %(same_nodes_same_move,same_nodes,len(multi)))
    if same_nodes and not multi:
        v.append("  -> CONFIRMS S-F22 on my boards: an identical node count always came with an identical move,")
        v.append("     so a node count is a sufficient identifier for the search result here.")
    elif multi:
        v.append("  -> REFUTES S-F22 here: node count matched while the MOVE differed, at %s."
                 %multi[:3])
        v.append("     That would mean equal volume of work can end at a different answer, so a node count is")
        v.append("     NOT a sufficient identifier - worth stating against the claim.")
    else:
        v.append("  -> INCONCLUSIVE: no two cells had equal node counts, so the implication was not testable.")
    (out/"check_plateau_general.json").write_text(json.dumps(
        {"summary":summary,"pairs":pairs,"same_nodes":same_nodes,
         "same_nodes_same_move":same_nodes_same_move,"multi_move_groups":[[n,list(b)] for n,b in multi],
         "verdict":v},indent=1))
    (out/"check_plateau_general.txt").write_text("\n".join(lines+v)+"\n")
    print(""); print("\n".join(v))

if __name__=="__main__":
    main()
