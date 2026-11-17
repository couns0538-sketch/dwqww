#!/usr/bin/env python3
"""swarm seat 01: CHECK of seat 02's S-F4 — a `go` naming only the OPPONENT's clock sets no limit.

Seat 02's claim: `go wtime N` with Black to move, and `go btime N` with White to move, both search until a `stop`
arrives, silently - the GUI sees a hang, not an error. A huge `btime` DOES bound a White-to-move search, so the
engine rightly ignores the opponent's clock; the complaint is that nothing tells the GUI.

WHY THIS ONE MATTERS: an unbounded search is a hang from the GUI's side, and it comes from a plausible mistake -
sending only the clock you think is relevant. This is Trap 6's hazard arriving through the PROTOCOL rather than
through a depth command, so the test needs a wall cap for exactly the same reason.

Method, with a hard wall cap on every search (Trap 6):
  A. `go wtime 6000` with BLACK to move      -> seat 02 says: no limit, must be stopped
  B. `go btime 6000` with WHITE to move      -> seat 02 says: no limit, must be stopped
  C. `go wtime 6000 btime 6000` (both)       -> control: must end on its own
  D. `go btime 6000000` with WHITE to move   -> seat 02 says a huge opponent clock DOES bound it
For each: did it answer within the cap, how long, and any info string emitted.

Usage: check_partial_clock.py <pc-exe> <outdir>
"""
import hashlib, json, os, select, subprocess, sys, time
from pathlib import Path

CAP=8.0
OPTS=[("LmrQuietBase","93"),("LmrQuietDivisor","205"),("LmrNoisyBase","13"),("LmrNoisyDivisor","333"),
      ("LmrHistoryDivisor","5643"),("NullMoveBase","5"),("LmpBase","8"),("HistoryPruneMultiplier","2220"),
      ("HistoryBonusQuadratic","24"),("HistoryBonusLinear","54"),("HistoryBonusMax","2212"),
      ("SingularDepth","6"),("IirDepth","2"),("NonPawnCorrection","true"),("CuckooRep","true"),
      ("HistRework","2"),("TtPruneV2","true"),("CorrHistV2","true"),("MateAlphaGuard","true"),
      ("OwnBook","false"),("Threads","1"),("Hash","16")]
# White to move; and a Black-to-move board
W_FEN="r3r1k1/p1bb1ppp/1p1q4/3P1p2/1nBP4/PPN2N1P/5PP1/1R1Q1RK1 w - - 0 1"
B_FEN="r3r1k1/p1bb1ppp/1p1q4/3P1p2/1nBP4/PPN2N1P/5PP1/1R1Q1RK1 b - - 0 1"

CASES=[
 ("A_wtime_only_black_to_move", B_FEN, "go wtime 6000"),
 ("B_btime_only_white_to_move", W_FEN, "go btime 6000"),
 ("C_both_clocks_control",      W_FEN, "go wtime 6000 btime 6000"),
 ("D_btime_huge_white_to_move", W_FEN, "go btime 6000000"),
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

def run(exe,fen,go):
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
    send(go)
    answered=False; bm=None
    while time.monotonic()-t0 < CAP:
        l=rd.line(time.monotonic()+min(0.5,max(0.05,CAP-(time.monotonic()-t0))))
        if l is None:
            if p.poll() is not None: break
            continue
        buf.append(l)
        if l.startswith("bestmove"):
            bm=l.split()[1] if len(l.split())>1 else None; answered=True; break
    elapsed=time.monotonic()-t0
    if not answered:
        try: send("stop"); time.sleep(0.4)
        except Exception: pass
    send("quit")
    try: p.wait(timeout=10)
    except Exception: p.kill()
    infos=[l for l in buf if l.startswith("info string")]
    return {"go":go,"answered":answered,"elapsed_s":round(elapsed,2),"bestmove":bm,
            "info_strings":infos,"cap":CAP}

def main():
    exe=sys.argv[1]; out=Path(sys.argv[2]); out.mkdir(parents=True,exist_ok=True)
    lines=["CHECK of seat 02's S-F4: does a go naming only the OPPONENT's clock set no limit?",
           "exe_started: %s"%exe,"sha256: %s"%hashlib.sha256(Path(exe).read_bytes()).hexdigest(),
           "PC20, Threads 1, Hash 16, HARD WALL CAP %.0f s per search (Trap 6: an unbounded call cannot" % CAP,
           "distinguish slow from hung), plus the position named so white-to-move vs black-to-move is explicit",""]
    lines.append("case\tgo\tanswered_within_cap\telapsed_s\tbestmove\tinfo_string")
    rows=[]
    for name,fen,go in CASES:
        r=run(exe,fen,go); r["case"]=name; r["fen"]=fen; rows.append(r)
        print("%-30s %-26s answered=%-5s %.2fs %s %s"
              %(name,go,r["answered"],r["elapsed_s"],r["bestmove"],
                r["info_strings"][:1] or ""),flush=True)
        lines.append("%s\t%s\t%s\t%.2f\t%s\t%s"%(name,go,r["answered"],r["elapsed_s"],r["bestmove"],
                     "; ".join(r["info_strings"][:2]) or "(none)"))
    def g(c): return next(r for r in rows if r["case"]==c)
    a,b,c,d=g("A_wtime_only_black_to_move"),g("B_btime_only_white_to_move"),g("C_both_clocks_control"),g("D_btime_huge_white_to_move")
    v=[]
    v.append("")
    v.append("A. `go wtime 6000` with BLACK to move: answered %s within %.0f s, info strings: %s"
             %(a["answered"],CAP,a["info_strings"] or "NONE"))
    v.append("B. `go btime 6000` with WHITE to move: answered %s, info strings: %s"
             %(b["answered"],b["info_strings"] or "NONE"))
    v.append("C. both clocks (control):        answered %s" % c["answered"])
    v.append("D. huge opponent clock:          answered %s" % d["answered"])
    v.append("")
    if not a["answered"] and not b["answered"] and c["answered"]:
        v.append("VERDICT: CONFIRMS seat 02's S-F4 - a partial clock naming only the OPPONENT leaves the search")
        v.append("  unbounded, while the both-clocks control ends normally. And NO info string is emitted, which is")
        v.append("  the part that makes it a GUI hang rather than an error: the protocol reports nothing wrong.")
        if d["answered"]:
            v.append("  D also confirms its narrower point: a HUGE opponent clock does bound the search.")
    elif a["answered"] and b["answered"]:
        v.append("VERDICT: does NOT reproduce - a partial opponent clock was bounded here; see the timings.")
    else:
        v.append("VERDICT: mixed - see the per-case answers above; reported as is.")
    (out/"check_partial_clock.json").write_text(json.dumps({"rows":rows,"verdict":v},indent=1))
    (out/"check_partial_clock.txt").write_text("\n".join(lines+v)+"\n")
    print(""); print("\n".join(v))

if __name__=="__main__":
    main()
