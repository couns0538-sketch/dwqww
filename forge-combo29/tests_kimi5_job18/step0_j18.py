#!/usr/bin/env python3
"""job 18 step 0: one fresh engine process per number; settings named only.
Usage: step0_j18.py <engine> <outdir>"""
import subprocess, sys, os, time, hashlib, re
ENG, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)
def opts(path):
    out=[]
    if path:
        for line in open(path):
            line=line.strip()
            if line and not line.startswith("#"):
                n,_,v=line.rpartition(" "); out.append((n.strip(),v))
    return out
def run(tag, optfile, cmd, stop):
    p=subprocess.Popen([ENG],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,bufsize=1)
    il=open(os.path.join(OUT,f"{tag}_input.log"),"w")
    def send(l):
        il.write(l+"\n"); il.flush(); p.stdin.write(l+"\n"); p.stdin.flush()
    lines=[]
    send("uci")
    while True:
        l=p.stdout.readline()
        if not l: raise RuntimeError("eof before uciok")
        lines.append(l.rstrip("\n"))
        if l.startswith("uciok"): break
    for n,v in opts(optfile):
        send(f"setoption name {n} value {v}")
    send("isready")
    while True:
        l=p.stdout.readline()
        if not l: raise RuntimeError("eof before readyok")
        lines.append(l.rstrip("\n"))
        if l.startswith("readyok"): break
    send(cmd)
    while True:
        l=p.stdout.readline()
        if not l: break
        lines.append(l.rstrip("\n"))
        if re.search(stop, l): break
    send("quit")
    try: p.wait(timeout=10)
    except Exception: p.kill()
    il.close()
    with open(os.path.join(OUT,f"{tag}.txt"),"w") as f:
        f.write("\n".join(lines)+"\n")
    print(tag, [l for l in lines if "nodes" in l or l.startswith("bench")][-1:] or lines[-1:])
t0=time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime())
run("none_bench11", None, "bench 11", r"info string bench depth")
run("none_bench13", None, "bench 13", r"info string bench depth")
run("none_bench16", None, "bench 16", r"info string bench depth")
run("none_perft5", None, "go perft 5", r"^nodes ")
run("s14_bench11", "s14.opt", "bench 11", r"info string bench depth")
run("s14_bench13", "s14.opt", "bench 13", r"info string bench depth")
run("pc20_bench11", "pc20.opt", "bench 11", r"info string bench depth")
run("pc20_bench13", "pc20.opt", "bench 13", r"info string bench depth")
with open(os.path.join(OUT,"step0.meta"),"w") as f:
    f.write(f"exe {ENG}\nsha256 {hashlib.sha256(open(ENG,'rb').read()).hexdigest()}\nstart {t0}\nend {time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())}\n")
