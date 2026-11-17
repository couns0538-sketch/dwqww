#!/usr/bin/env python3
"""softnodes_run.py : TWO fresh processes per position with `go softnodes 2000` (the self-play command)."""
import re, subprocess, sys, time
INFO=re.compile(r"^info depth (\d+) .*?score (cp|mate) (-?\d+).*?nodes (\d+)")
PC="/home/ubuntu/pcbuild/forge"
OPTS=[l.strip() for l in open("pc20_opts.txt") if l.strip() and not l.startswith("#")]+["setoption name OwnBook value false"]
FENS=[l.strip() for l in open(sys.argv[1]) if l.strip()]
def run(fen):
    p=subprocess.Popen([PC],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,bufsize=1)
    p.stdin.write("uci\n");p.stdin.flush()
    names=set()
    while True:
        l=p.stdout.readline()
        if not l: raise RuntimeError("died")
        s=l.strip()
        if s.startswith("option name "): names.add(s.split("option name ")[1].split(" type ")[0])
        if s=="uciok": break
    for line in OPTS:
        nm=line.split("name ")[1].split(" value ")[0]
        if nm not in names: raise RuntimeError("STOP "+nm)
        p.stdin.write(line+"\n");p.stdin.flush()
        p.stdin.write("isready\n");p.stdin.flush()
        while p.stdout.readline().strip()!="readyok": pass
    p.stdin.write("ucinewgame\n");p.stdin.flush()
    p.stdin.write("position fen "+fen+"\n");p.stdin.flush()
    p.stdin.write("isready\n");p.stdin.flush()
    while p.stdout.readline().strip()!="readyok": pass
    p.stdin.write("go softnodes 2000\n");p.stdin.flush()
    last=None; bm=None; partial=False; seen={}
    while True:
        l=p.stdout.readline()
        if not l: raise RuntimeError("died in search")
        s=l.strip()
        m=INFO.match(s)
        if m:
            d=int(m.group(1)); seen[d]=seen.get(d,0)+1
            if seen[d]>1: partial=True
            last=(d,m.group(2),int(m.group(3)),int(m.group(4)))
        if s.startswith("bestmove"): bm=s.split()[1]; break
    p.stdin.write("quit\n");p.stdin.flush()
    try: p.wait(timeout=10)
    except: p.kill()
    return last,bm,partial
print("| # | position | proc A: move/nodes/depth | proc B: move/nodes/depth | same? |")
print("|---|---|---|---|---|")
dis=0; nodesdiff=0; over=0; depths={}
for i,fen in enumerate(FENS,1):
    a=run(fen); b=run(fen)
    same_move = a[1]==b[1]
    same_nodes = a[0][3]==b[0][3]
    if not same_move: dis+=1
    if not same_nodes: nodesdiff+=1
    if a[0][3]>2000: over+=1
    depths[a[0][0]]=depths.get(a[0][0],0)+1
    print("| %d | %s | %s/%d/%d | %s/%d/%d | %s |"%(i,fen[:26],a[1],a[0][3],a[0][0],
          b[1],b[0][3],b[0][0],"yes" if (same_move and same_nodes) else "**NO**"))
print()
print("P1 move disagreements: %d of %d"%(dis,len(FENS)))
print("P2 node-count disagreements: %d of %d"%(nodesdiff,len(FENS)))
print("P3 runs with nodes > 2000: %d of %d"%(over,len(FENS)))
print("depth distribution:", dict(sorted(depths.items())))
