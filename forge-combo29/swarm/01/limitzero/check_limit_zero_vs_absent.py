#!/usr/bin/env python3
"""swarm seat 01: CHECK of seat 25's S-F37 — a "minimum one" floor across the UCI limit fields.

Seat 25's claim: `go depth 0` behaves as depth 1; `go movetime 0` still reaches a depth (it saw 5);
`go nodes 0` answers immediately at depth 0 with a DIFFERENT move. So depth and movetime clamp 0 upward while
nodes honours it literally as "no search".

Seat 25 flags its own caveat: its probe is a SCOPE result, not a 0-versus-ABSENT result. That is the gap worth
closing, and it is the one that matters to a harness, because the two questions are different:

    "what does 0 do?"          seat 25 answers this
    "is 0 the same as absent?" this is what a harness actually needs to know

If `go depth 0` searches one ply and `go depth` (absent) searches to the default, they are NOT the same, and a
harness that omits the field gets a very different search from one that sends 0. If they ARE the same, then 0 is
effectively "unset" and the floor is harmless.

So this measures each field in THREE forms: value 0, the field ABSENT, and a normal value as control.

Usage: check_limit_zero_vs_absent.py <pc-exe> <outdir>
"""
import hashlib, json, os, select, subprocess, sys, time
from pathlib import Path

TIMEOUT=180.0
OPTS=[("LmrQuietBase","93"),("LmrQuietDivisor","205"),("LmrNoisyBase","13"),("LmrNoisyDivisor","333"),
      ("LmrHistoryDivisor","5643"),("NullMoveBase","5"),("LmpBase","8"),("HistoryPruneMultiplier","2220"),
      ("HistoryBonusQuadratic","24"),("HistoryBonusLinear","54"),("HistoryBonusMax","2212"),
      ("SingularDepth","6"),("IirDepth","2"),("NonPawnCorrection","true"),("CuckooRep","true"),
      ("HistRework","2"),("TtPruneV2","true"),("CorrHistV2","true"),("MateAlphaGuard","true"),
      ("OwnBook","false"),("Threads","1"),("Hash","16")]
BOARD="r3r1k1/p1bb1ppp/1p1q4/3P1p2/1nBP4/PPN2N1P/5PP1/1R1Q1RK1 b - - 0 1"

CASES=[
 ("depth_0",      "go depth 0"),
 ("depth_absent", "go infinite"),
 ("depth_5",      "go depth 5"),
 ("movetime_0",   "go movetime 0"),
 ("movetime_50",  "go movetime 50"),
 ("nodes_0",      "go nodes 0"),
 ("nodes_20000",  "go nodes 20000"),
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

def run(exe,go,stop_after=None):
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
    t0=time.monotonic()
    send(go)
    dl=[]; bm=None
    # `go infinite` never answers on its own: stop it after a fixed slice so the row is comparable
    deadline=time.monotonic()+(2.0 if go=="go infinite" else TIMEOUT)
    if go=="go infinite":
        time.sleep(1.0)
        send("stop")
    while True:
        l=rd.line(deadline)
        if l is None: break
        if l.startswith("info depth"): dl.append(l)
        if l.startswith("bestmove"):
            bm=l.split()[1] if len(l.split())>1 else None; break
    wall=(time.monotonic()-t0)*1000.0
    send("quit")
    try: p.wait(timeout=30)
    except Exception: p.kill()
    depth=None; nodes=None
    for l in reversed(dl):
        f=l.split()
        if depth is None and "depth" in f: depth=int(f[f.index("depth")+1])
        if nodes is None and "nodes" in f: nodes=int(f[f.index("nodes")+1])
        if depth is not None and nodes is not None: break
    return {"go":go,"depth":depth,"nodes":nodes,"bestmove":bm,"wall_ms":round(wall,1),
            "n_lines":len(dl),"answered":bm is not None}

def main():
    exe=sys.argv[1]; out=Path(sys.argv[2]); out.mkdir(parents=True,exist_ok=True)
    lines=["CHECK of seat 25's S-F37: does 0 clamp, and is 0 the SAME as ABSENT?",
           "exe_started: %s"%exe,"sha256: %s"%hashlib.sha256(Path(exe).read_bytes()).hexdigest(),
           "board: "+BOARD,"PC20, Threads 1, Hash 16, fresh process per row",
           "seat 25's own caveat: its probe was a scope result, not 0-versus-absent - that is the gap closed here",""]
    lines.append("case\tgo\tdepth\tnodes\twall_ms\tbestmove\tanswered")
    rows=[]
    for name,go in CASES:
        r=run(exe,go); r["case"]=name; rows.append(r)
        print("%-14s %-16s depth %-3s nodes %-8s wall %-8s %-6s %s"
              %(name,go,r["depth"],r["nodes"],r["wall_ms"],r["bestmove"],r["answered"]),flush=True)
        lines.append("%s\t%s\t%s\t%s\t%s\t%s\t%s"%(name,go,r["depth"],r["nodes"],r["wall_ms"],
                     r["bestmove"],r["answered"]))
    def g(n): return next((r for r in rows if r["case"]==n),None)
    v=[]
    d0,dA,d5=g("depth_0"),g("depth_absent"),g("depth_5")
    m0,m50=g("movetime_0"),g("movetime_50")
    n0,n20=g("nodes_0"),g("nodes_20000")
    v.append("")
    v.append("DEPTH:   go depth 0 -> depth %s (%s nodes) ; absent/infinite -> depth %s (%s nodes) after a 1 s stop ; go depth 5 -> %s"
             %(d0["depth"],d0["nodes"],dA["depth"],dA["nodes"],d5["depth"]))
    v.append("MOVETIME: go movetime 0 -> depth %s (%s nodes, %s ms) ; go movetime 50 -> depth %s (%s nodes)"
             %(m0["depth"],m0["nodes"],m0["wall_ms"],m50["depth"],m50["nodes"]))
    v.append("NODES:    go nodes 0 -> depth %s (%s nodes), move %s ; go nodes 20000 -> depth %s, move %s"
             %(n0["depth"],n0["nodes"],n0["bestmove"],n20["depth"],n20["bestmove"]))
    v.append("")
    clamped = d0["depth"] is not None and d0["depth"]>=1
    if clamped:
        v.append("CONFIRMS seat 25 on depth: `go depth 0` searched %s ply/plies rather than declining."%d0["depth"])
    if m0["depth"] is not None and m0["depth"]>=1:
        v.append("CONFIRMS seat 25 on movetime: `go movetime 0` still reached depth %s (%s nodes) - a floor, not zero time."
                 %(m0["depth"],m0["nodes"]))
    if n0["answered"] and n0["nodes"]==0:
        v.append("CONFIRMS seat 25 on nodes: `go nodes 0` answered at 0 nodes with move %s (control: %s)."
                 %(n0["bestmove"],n20["bestmove"]))
    v.append("")
    # the gap seat 25 left open
    same = (d0["depth"]==dA["depth"])
    v.append("THE 0-VERSUS-ABSENT QUESTION seat 25 left open:")
    v.append("  go depth 0 -> depth %s ; a search with NO depth limit (go infinite, stopped at 1 s) -> depth %s"
             %(d0["depth"],dA["depth"]))
    if same:
        v.append("  -> 0 and ABSENT give the same depth, so depth 0 behaves like 'no limit', not like 'one ply'.")
        v.append("     That is a different statement from seat 25's and would mean the floor is harmless.")
    else:
        v.append("  -> 0 and ABSENT differ: depth 0 clamps to ONE PLY while omitting the field searches freely.")
        v.append("     So a harness that sends `depth 0` to mean 'no limit' gets a one-ply search - the floor is")
        v.append("     NOT harmless, and this confirms seat 25's reading while closing its caveat.")
    (out/"check_limit_zero_vs_absent.json").write_text(json.dumps({"rows":rows,"verdict":v},indent=1))
    (out/"check_limit_zero_vs_absent.txt").write_text("\n".join(lines+v)+"\n")
    print(""); print("\n".join(v))

if __name__=="__main__":
    main()
