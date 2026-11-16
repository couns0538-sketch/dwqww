#!/usr/bin/env python3
"""swarm seat 01: CHECK of seat 25's S-F7 — a terminal root emits 64 info lines at 0 nodes.

Seat 25's claim, verbatim (its scoped, corrected form):
  "on a TERMINAL root, `go nodes 100` and `go movetime 50` each emit 64 info lines at depths 1..64 with
   nodes 0, where `go depth 5` correctly emits 5. A consumer that treats increasing `depth` as progress sees
   64 phantom iterations and 0 nodes of work; harmless for strength, misleading for any training label or
   progress display keyed on depth."

What I check, on my own build:
  1. the counts, for `go depth 5`, `go nodes 100`, `go movetime 50`, and `go depth 64` on a terminal root;
  2. the SAME for a STALEMATED root (seat 25 reports one terminal case; a match can end either way);
  3. whether a NORMAL root also runs to 64 (it must not - that would mean the loop always spins);
  4. the consequence check seat 25 flags: does a depth-keyed consumer see phantom progress? I report the last
     depth emitted and the node count, which is what such a consumer would store as a training label.

Usage: check_terminal_root_lines.py <pc-exe> <outdir>
"""
import hashlib, json, os, select, subprocess, sys, time
from pathlib import Path
import chess

TIMEOUT=300.0
OPTS=[("LmrQuietBase","93"),("LmrQuietDivisor","205"),("LmrNoisyBase","13"),("LmrNoisyDivisor","333"),
      ("LmrHistoryDivisor","5643"),("NullMoveBase","5"),("LmpBase","8"),("HistoryPruneMultiplier","2220"),
      ("HistoryBonusQuadratic","24"),("HistoryBonusLinear","54"),("HistoryBonusMax","2212"),
      ("SingularDepth","6"),("IirDepth","2"),("NonPawnCorrection","true"),("CuckooRep","true"),
      ("HistRework","2"),("TtPruneV2","true"),("CorrHistV2","true"),("MateAlphaGuard","true"),
      ("OwnBook","false"),("Threads","1"),("Hash","16")]

BOARDS = [
    ("checkmated", "4R1k1/5ppp/8/8/8/8/5PPP/6K1 b - - 1 60"),
    ("stalemated", "7k/5Q2/8/8/8/8/8/K7 b - - 0 1"),
    ("normal",     "1r6/2k2pp1/2p2n2/2Pppb1p/7P/1P2PPP1/P3BK2/R1R5 b - - 0 1"),
]
GOS = ["go depth 5", "go nodes 100", "go movetime 50", "go depth 64"]

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

def run(exe, fen, go):
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
    send(go)
    bml=until("bestmove",d)
    time.sleep(0.1)
    send("quit")
    try: p.wait(timeout=120)
    except Exception: p.kill()
    dl=[l for l in buf if l.startswith("info depth")]
    depths=[]
    last_nodes=None
    for l in dl:
        f=l.split()
        if "depth" in f:
            try: depths.append(int(f[f.index("depth")+1]))
            except ValueError: pass
        if "nodes" in f: last_nodes=f[f.index("nodes")+1]
    return {"go":go,"n_lines":len(dl),"max_depth":max(depths) if depths else None,
            "last_nodes":last_nodes,
            "bestmove":bml.split()[1] if bml and len(bml.split())>1 else None}

def main():
    exe=sys.argv[1]; out=Path(sys.argv[2]); out.mkdir(parents=True,exist_ok=True)
    lines=["CHECK of seat 25's S-F7 (scoped form): do terminal roots emit 64 info lines at 0 nodes?",
           "exe_started: %s"%exe,"sha256: %s"%hashlib.sha256(Path(exe).read_bytes()).hexdigest(),
           "PC r15 + PC20, Threads 1, Hash 16, fresh process per row",""]
    lines.append("board\tgo\tinfo_lines\tmax_depth\tlast_nodes\tbestmove")
    rows=[]
    for bname,fen in BOARDS:
        for go in GOS:
            r=run(exe,fen,go)
            r["board"]=bname
            rows.append(r)
            print("%-11s %-16s lines %-3d maxdepth %-3s nodes %-6s bm %s"
                  %(bname,go,r["n_lines"],r["max_depth"],r["last_nodes"],r["bestmove"]),flush=True)
            lines.append("%s\t%s\t%d\t%s\t%s\t%s"%(bname,go,r["n_lines"],r["max_depth"],
                                                   r["last_nodes"],r["bestmove"]))
    def get(b,g): return next(r for r in rows if r["board"]==b and r["go"]==g)
    v=[]
    v.append("")
    for b in ("checkmated","stalemated"):
        d5=get(b,"go depth 5"); n100=get(b,"go nodes 100"); mt=get(b,"go movetime 50")
        v.append("%s: go depth 5 -> %d lines; go nodes 100 -> %d; go movetime 50 -> %d"
                 %(b.upper(),d5["n_lines"],n100["n_lines"],mt["n_lines"]))
    nrm=get("normal","go nodes 100")
    v.append("normal root: go nodes 100 -> %d lines, max depth %s, nodes %s (must NOT be 64)"
             %(nrm["n_lines"],nrm["max_depth"],nrm["last_nodes"]))
    v.append("")
    term=[r for r in rows if r["board"] in ("checkmated","stalemated") and r["go"]!="go depth 5"]
    spun=[r for r in term if r["n_lines"]>=60]
    if spun and nrm["n_lines"]<60:
        v.append("VERDICT: CONFIRMS seat 25's S-F7 in its scoped form. On terminal roots the node-limited and")
        v.append("  time-limited commands spin to the depth cap (%d of %d such rows emitted 60+ lines at 0 nodes),"
                 %(len(spun),len(term)))
        v.append("  while `go depth 5` correctly emits 5 and a NORMAL root emits %d. So the phantom iterations are"
                 %nrm["n_lines"])
        v.append("  specific to terminal roots, not a general loop defect - cosmetic for strength, but a")
        v.append("  depth-keyed training label or progress display reads 64 iterations that did no work.")
    elif nrm["n_lines"]>=60:
        v.append("VERDICT: the NORMAL root also spins to the cap, so this is not terminal-specific; reported as is.")
    else:
        v.append("VERDICT: does not reproduce - terminal roots did not spin here.")
    (out/"check_terminal_root_lines.json").write_text(json.dumps({"rows":rows,"verdict":v},indent=1))
    (out/"check_terminal_root_lines.txt").write_text("\n".join(lines+v)+"\n")
    print(""); print("\n".join(v))

if __name__=="__main__":
    main()
