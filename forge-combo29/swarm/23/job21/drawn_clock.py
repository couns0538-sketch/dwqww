#!/usr/bin/env python3
"""drawn_clock.py : the drawn-root repair on the paths matches actually use (clock, softnodes), not just `go depth`."""
import re, subprocess
INFO=re.compile(r"^info depth (\d+) .*?score (cp|mate) (-?\d+).*?nodes (\d+)")
BASE="/home/ubuntu/build/forge"; PC="/home/ubuntu/pcbuild/forge"
OPTS=[l.strip() for l in open("../job7/pc20_opts.txt") if l.strip() and not l.startswith("#")]+["setoption name OwnBook value false"]
ROOT="1K6/8/8/3R4/8/8/8/k7 w - - 0 1"
MOVES="d5d6 a1b1 d6d5 b1a1 d5d6 a1b1 d6d5 b1a1"

def run(exe, budget, opts=None):
    p=subprocess.Popen([exe],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,bufsize=1)
    p.stdin.write("uci\n");p.stdin.flush()
    names=set()
    while True:
        l=p.stdout.readline()
        if not l: raise RuntimeError("died")
        s=l.strip()
        if s.startswith("option name "): names.add(s.split("option name ")[1].split(" type ")[0])
        if s=="uciok": break
    use = OPTS if opts is None else opts
    for line in use:
        nm=line.split("name ")[1].split(" value ")[0]
        if nm not in names: raise RuntimeError("STOP option "+nm)
        p.stdin.write(line+"\n");p.stdin.flush()
        p.stdin.write("isready\n");p.stdin.flush()
        while p.stdout.readline().strip()!="readyok": pass
    p.stdin.write("ucinewgame\n");p.stdin.flush()
    p.stdin.write("position fen %s moves %s\n"%(ROOT,MOVES));p.stdin.flush()
    p.stdin.write("isready\n");p.stdin.flush()
    while p.stdout.readline().strip()!="readyok": pass
    p.stdin.write(budget+"\n");p.stdin.flush()
    last=None; bm=None
    while True:
        l=p.stdout.readline()
        if not l: break
        s=l.strip()
        m=INFO.match(s)
        if m: last=(m.group(2),int(m.group(3)),int(m.group(4)))
        if s.startswith("bestmove"): bm=s.split()[1]; break
    p.stdin.write("quit\n");p.stdin.flush()
    try: p.wait(timeout=10)
    except: p.kill()
    return last, bm

BUDGETS=[("go depth 8","depth 8"),("go wtime 6000 btime 6000 winc 60 binc 60","clock 6s"),
         ("go softnodes 2000","softnodes 2000")]
print("threefold-repetition root, reached by the real move list; Threads 1, Hash 16, OwnBook false")
print()
print("| path | base | PC r15 + PC20 |")
print("|---|---|---|")
rows={}
for cmd,label in BUDGETS:
    # the base build has no PC20 options: give it none, and OwnBook false only
    base_opts=["setoption name OwnBook value false"]
    b,bm_b=run(BASE,cmd,base_opts); p_,bm_p=run(PC,cmd)
    def fmt(r,bm):
        if r is None: return "no info line (%s)"%bm
        return "%s %d, %d nodes, %s"%(r[0],r[1],r[2],bm)
    print("| %s | %s | %s |"%(label,fmt(b,bm_b),fmt(p_,bm_p)))
    rows[label]=(b,p_)
print()
for label,(b,p_) in rows.items():
    print("%-14s base 0 nodes? %-5s | PC 0 nodes? %s"%(label, b is not None and b[2]==0, p_ is not None and p_[2]==0))
