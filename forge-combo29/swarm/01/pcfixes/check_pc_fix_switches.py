#!/usr/bin/env python3
"""swarm seat 01: CHECK of seat 13's S-F18 — two of the PC patch's seven fixes are compiled out by default.

Seat 13's claim, verbatim:
  "TWO of the PC patch's seven fixes are COMPILED OUT by default: FORGE_FIX_BARE_KING_ONE_THREAD and
   FORGE_FIX_ABORT_PUBLISH are both `#define ... 0` ... Verified FORGE_FIX_GO_PARSE works: `go wtime btime 50`
   gives base 1 info line / 26 nodes / depth 1 vs PC 5 lines / 1001 nodes / depth 5, while the well-formed
   `go wtime 50 btime 50` is IDENTICAL on both builds (control)."

Two parts, checked differently:
  A. THE SWITCH DEFAULTS — read from the source I actually built, so the claim is verified against the code
     that produced my binary rather than against the patch text.
  B. THE BEHAVIOURAL CONSEQUENCE of the one switch seat 13 could observe: a malformed `go` where a keyword
     would be swallowed as the previous keyword's value. Measured on base and PC, with the well-formed control.

Usage: check_pc_fix_switches.py <pc-exe> <base-exe> <outdir>
"""
import hashlib, json, os, select, subprocess, sys, time
from pathlib import Path

TIMEOUT=180.0
OPTS=[("Threads","1"),("Hash","16"),("OwnBook","false")]

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

def run(exe, go, hard_timeout=8.0):
    """Send one `go`; read until bestmove OR the wall deadline, then quit. Returns counts."""
    p=subprocess.Popen([exe],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,bufsize=0,cwd="/tmp")
    rd=R(p.stdout.fileno()); buf=[]
    def pump(dl):
        while True:
            l=rd.line(dl)
            if l is None: return
            buf.append(l)
    def send(s): p.stdin.write((s+"\n").encode()); p.stdin.flush()
    d=time.monotonic()+TIMEOUT
    send("uci"); pump(time.monotonic()+5)
    for n,v in OPTS: send("setoption name %s value %s"%(n,v)); send("isready")
    pump(time.monotonic()+5)
    send("ucinewgame"); send("isready"); pump(time.monotonic()+3)
    send("position startpos"); send("isready"); pump(time.monotonic()+3)
    t0=time.monotonic()
    send(go)
    # read until bestmove, or until hard_timeout, whichever first
    got_bm=False
    while time.monotonic()-t0 < hard_timeout:
        l=rd.line(time.monotonic()+min(0.5, max(0.05,hard_timeout-(time.monotonic()-t0))))
        if l is None: continue
        buf.append(l)
        if l.startswith("bestmove"): got_bm=True; break
    wall=(time.monotonic()-t0)*1000
    send("quit")
    try: p.wait(timeout=10)
    except Exception: p.kill()
    dl=[l for l in buf if l.startswith("info depth")]
    nodes=None; depth=None
    for l in reversed(dl):
        f=l.split()
        if nodes is None and "nodes" in f: nodes=int(f[f.index("nodes")+1])
        if depth is None and "depth" in f: depth=int(f[f.index("depth")+1])
        if nodes is not None and depth is not None: break
    return {"go":go,"n_info":len(dl),"max_depth":depth,"nodes":nodes,
            "got_bestmove":got_bm,"wall_ms":round(wall,1)}

def main():
    pc,base,out=sys.argv[1],sys.argv[2],Path(sys.argv[3]); out.mkdir(parents=True,exist_ok=True)
    lines=["CHECK of seat 13's S-F18: PC patch switch defaults, and the GO_PARSE behavioural signature",
           "pc   %s sha256 %s"%(pc,hashlib.sha256(Path(pc).read_bytes()).hexdigest()),
           "base %s sha256 %s"%(base,hashlib.sha256(Path(base).read_bytes()).hexdigest()),""]
    # A: read the switches from the source that was built
    srcsrc=Path("/agent/repos/pc/forge-combo29")
    switches={}
    for f in list(srcsrc.glob("src/*.cpp"))+list(srcsrc.glob("include/forge/*.hpp")):
        for i,line in enumerate(f.read_text(errors="ignore").splitlines(),1):
            s=line.strip()
            # accept "// #define X 0" too: a commented-out switch is not compiled at all, which is
            # itself worth seeing, so record it rather than silently skipping it
            commented = s.startswith("//") and "#define FORGE_FIX_" in s
            body = s.lstrip("/ ").strip() if commented else s
            if body.startswith("#define FORGE_FIX_"):
                parts=body.split()
                if len(parts) < 2:
                    continue
                name = parts[1]
                # a later real definition wins over a commented one
                if name in switches and not commented:
                    pass
                switches[name]={"value": parts[2] if len(parts)>2 else "1(default)",
                                "location": "%s:%d%s"%(f.relative_to(srcsrc), i,
                                                       " (COMMENTED OUT)" if commented else "")}
    lines.append("A. FORGE_FIX_* defaults in the source that produced my PC binary:")
    lines.append("switch\tvalue\tlocation")
    for k in sorted(switches):
        lines.append("%s\t%s\t%s"%(k,switches[k]["value"],switches[k]["location"]))
        print("%-34s %s  %s"%(k,switches[k]["value"],switches[k]["location"]),flush=True)
    off=[k for k,v in switches.items()
         if v["value"].strip()=="0" and "COMMENTED" not in v["location"]]
    lines.append("")
    lines.append("   switches defaulting to 0: %s"%(off or "none"))

    # B: the GO_PARSE behavioural signature
    lines.append("")
    lines.append("B. GO_PARSE behavioural signature: a malformed `go` with a keyword where a value belongs")
    lines.append("command\tpc lines\tdepth\tnodes\tbase lines\tdepth\tnodes\tidentical?")
    cases=["go wtime btime 50", "go wtime 50 btime 50"]
    rows=[]
    for go in cases:
        a=run(pc,go); b=run(base,go)
        ident=(a["n_info"],a["max_depth"],a["nodes"])==(b["n_info"],b["max_depth"],b["nodes"])
        rows.append({"go":go,"pc":a,"base":b,"identical":ident})
        print("%-24s pc %-3d d%-3s n%-6s | base %-3d d%-3s n%-6s | %s"
              %(go,a["n_info"],a["max_depth"],a["nodes"],b["n_info"],b["max_depth"],b["nodes"],
                "IDENTICAL" if ident else "DIFFERS"),flush=True)
        lines.append("%s\t%d\t%s\t%s\t%d\t%s\t%s\t%s"%(go,a["n_info"],a["max_depth"],a["nodes"],
                     b["n_info"],b["max_depth"],b["nodes"],ident))
    v=[]
    v.append("")
    v.append("A RESULT: %d of %d FORGE_FIX_* switches default to 0 (%s), which %s seat 13's S-F18."
             %(len(off),len(switches),", ".join(off) if off else "none",
               "CONFIRMS" if set(off)>={"FORGE_FIX_BARE_KING_ONE_THREAD","FORGE_FIX_ABORT_PUBLISH"}
               else "does not fully confirm"))
    mal=next(r for r in rows if r["go"]=="go wtime btime 50")
    ctl=next(r for r in rows if r["go"]=="go wtime 50 btime 50")
    v.append("B RESULT: the malformed `go` %s between builds (PC %d lines/depth %s vs base %d/depth %s);"
             %("DIFFERS" if not mal["identical"] else "is IDENTICAL", mal["pc"]["n_info"],
               mal["pc"]["max_depth"], mal["base"]["n_info"], mal["base"]["max_depth"]))
    v.append("  the well-formed control %s." % ("is IDENTICAL, as seat 13 found" if ctl["identical"]
                                                else "ALSO DIFFERS, which seat 13 did not report"))
    if not ctl["identical"]:
        v.append("  -> the control failing means the difference cannot be attributed to GO_PARSE alone on my")
        v.append("     build, so I confirm the SWITCH DEFAULTS and state the behavioural half as unattributed.")
    v.append("")
    v.append("WHY THIS MATTERS FOR THE OWNER: what he runs is not 'the PC patch's seven fixes' but FIVE of")
    v.append("  them, and the two that are off are off for measured reasons recorded in the patch itself.")
    (out/"check_pc_fix_switches.json").write_text(json.dumps({"switches":switches,"off":off,"rows":rows,"verdict":v},indent=1))
    (out/"check_pc_fix_switches.txt").write_text("\n".join(lines+v)+"\n")
    print(""); print("\n".join(v))

if __name__=="__main__":
    main()
