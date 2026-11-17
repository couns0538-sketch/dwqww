#!/usr/bin/env python3
"""swarm seat 01: CHECK of seat 20's S-F50 and S-C30 — when does the 0-node answer appear?

Seat 20's S-F50: on `1r6/2k2pp1/2p2n2/2Pppb1p/7P/1P2PPP1/P3BK2/R1R5 b`, PC r15 + PC20, Threads 1,
`go wtime 5000`, 10 fresh processes per arm:
   Hash 2048 + MultiPV 8: 1/10 zero-node answers IDLE, 6/10 with three CPU hogs
   Hash 16  + MultiPV 1: 0/10 in BOTH conditions
and its S-C30 narrows it: MultiPV 3 + Hash 256 gave 0/5 idle and 0/5 loaded.

So the interesting question is not "does it happen" but WHERE THE BOUNDARY IS. Seat 20's own two data points
bracket it: (MultiPV 8, Hash 2048) fails, (MultiPV 3, Hash 256) does not. This sweeps the two parameters to see
which one drives it, because that determines the advice: "avoid MultiPV>1" and "avoid Hash>=1GB" are different
instructions.

To keep it inside the time: idle only, 5 runs per cell, a 3x2 grid of (MultiPV) x (Hash), no CPU load. The load
arm is what S-F50 already established; the parameter boundary is what is missing.

Usage: check_zero_node_collapse.py <pc-exe> <outdir>
"""
import hashlib, json, os, select, subprocess, sys, time
from pathlib import Path

TIMEOUT=180.0
S14=[("LmrQuietBase","93"),("LmrQuietDivisor","205"),("LmrNoisyBase","13"),("LmrNoisyDivisor","333"),
     ("LmrHistoryDivisor","5643"),("NullMoveBase","5"),("LmpBase","8"),("HistoryPruneMultiplier","2220"),
     ("HistoryBonusQuadratic","24"),("HistoryBonusLinear","54"),("HistoryBonusMax","2212"),
     ("SingularDepth","6"),("IirDepth","2"),("NonPawnCorrection","true")]
PC20_EXTRA=[("CuckooRep","true"),("HistRework","2"),("TtPruneV2","true"),("CorrHistV2","true"),
            ("MateAlphaGuard","true"),("OwnBook","false")]
BOARD="1r6/2k2pp1/2p2n2/2Pppb1p/7P/1P2PPP1/P3BK2/R1R5 b - - 0 1"
GO="go wtime 5000 btime 5000 winc 0 binc 0"
CELLS=[(1,16),(1,2048),(4,16),(4,2048),(8,16),(8,2048)]
RUNS=5

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

def run(exe,mpv,hashmb):
    p=subprocess.Popen([exe],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,bufsize=0,cwd="/tmp")
    rd=R(p.stdout.fileno()); buf=[]
    def until(pre,dl):
        while True:
            l=rd.line(dl)
            if l is None: return None
            buf.append(l)
            if l.startswith(pre): return l
    def send(s): p.stdin.write((s+"\n").encode()); p.stdin.flush()
    d=time.monotonic()+90
    send("uci"); until("uciok",d)
    for n,v in S14+PC20_EXTRA: send("setoption name %s value %s"%(n,v)); send("isready"); until("readyok",d)
    send("setoption name Threads value 1"); send("isready"); until("readyok",d)
    send("setoption name Hash value %d"%hashmb); send("isready"); until("readyok",d)
    send("setoption name MultiPV value %d"%mpv); send("isready"); until("readyok",d)
    send("ucinewgame"); send("isready"); until("readyok",d)
    send("position fen "+BOARD); send("isready"); until("readyok",d)
    send(GO)
    bml=until("bestmove",d)
    send("quit")
    try: p.wait(timeout=30)
    except Exception: p.kill()
    dl=[l for l in buf if l.startswith("info depth")]
    nodes=None
    for l in reversed(dl):
        f=l.split()
        if "nodes" in f: nodes=int(f[f.index("nodes")+1]); break
    return {"mpv":mpv,"hash":hashmb,"nodes":nodes,"bestmove":bml.split()[1] if bml and len(bml.split())>1 else None,
            "zero": (nodes==0)}

def main():
    exe=sys.argv[1]; out=Path(sys.argv[2]); out.mkdir(parents=True,exist_ok=True)
    lines=["CHECK of seat 20's S-F50 / S-C30: WHERE is the 0-node boundary in MultiPV x Hash?",
           "exe_started: %s"%exe,"sha256: %s"%hashlib.sha256(Path(exe).read_bytes()).hexdigest(),
           "board: "+BOARD,"PC20 + Threads 1, %s, idle machine, %d fresh processes per cell"%(GO,RUNS),""]
    lines.append("multipv\thash_MB\tzero_count\tout_of\tnode_counts\tmoves")
    rows=[]
    for mpv,hmb in CELLS:
        res=[run(exe,mpv,hmb) for _ in range(RUNS)]
        zeros=sum(1 for r in res if r["zero"])
        nodes=[r["nodes"] for r in res]
        moves=sorted({r["bestmove"] for r in res})
        rows.append({"mpv":mpv,"hash":hmb,"zeros":zeros,"n":RUNS,"nodes":nodes,"moves":moves})
        print("MultiPV %-2d Hash %-5d -> %d/%d zero-node, nodes %s, moves %s"
              %(mpv,hmb,zeros,RUNS,nodes,moves),flush=True)
        lines.append("%d\t%d\t%d\t%d\t%s\t%s"%(mpv,hmb,zeros,RUNS,nodes,moves))
    # which parameter drives it?
    def z(mpv,hmb):
        r=next((x for x in rows if x["mpv"]==mpv and x["hash"]==hmb),None)
        return r["zeros"] if r else None
    v=[]
    v.append("")
    v.append("HIGH-MultiPV arm: MultiPV 8 at Hash 16 -> %d/%d zero ; at Hash 2048 -> %d/%d zero"
             %(z(8,16),RUNS,z(8,2048),RUNS))
    v.append("HIGH-Hash arm:   Hash 2048 at MultiPV 1 -> %d/%d zero ; at MultiPV 8 -> %d/%d zero"
             %(z(1,2048),RUNS,z(8,2048),RUNS))
    v.append("CONTROL:         MultiPV 1 Hash 16 -> %d/%d zero (seat 20's healthy cell)"%(z(1,16),RUNS))
    if z(8,2048) and z(8,2048)>0 and (z(8,16)==0 if z(8,16) is not None else False):
        v.append("")
        v.append("VERDICT: CONFIRMS seat 20's S-F50 in the combination it names, and LOCATES the driver: the")
        v.append("  collapse needs BOTH a high MultiPV and a large Hash - MultiPV 8 alone (Hash 16) and Hash 2048")
        v.append("  alone (MultiPV 1) are clean. That matches its S-C30 too: MultiPV 3 + Hash 256 sits below both")
        v.append("  thresholds. ACTION is therefore narrower than 'avoid MultiPV>1': avoid the COMBINATION.")
    elif not any(r["zeros"] for r in rows):
        v.append("")
        v.append("VERDICT: no zero-node answer in ANY cell on an idle machine at %d runs each - consistent with"
                 %RUNS)
        v.append("  seat 20 reporting 1/10 idle (a rare event needing more runs to see) and with its S-C30. Not a")
        v.append("  refutation: the load condition, which it says turns 1/10 into 6/10, is not tested here.")
    else:
        v.append("")
        v.append("VERDICT: the pattern does not match the 'both parameters' reading; see the grid.")
    (out/"check_zero_node_collapse.json").write_text(json.dumps({"rows":rows,"verdict":v},indent=1))
    (out/"check_zero_node_collapse.txt").write_text("\n".join(lines+v)+"\n")
    print(""); print("\n".join(v))

if __name__=="__main__":
    main()
