#!/usr/bin/env python3
"""switches.py : do the PC20 search switches change any MOVE? A = S14 only, B = PC20, C = S14+CorrHistV2."""
import re, subprocess, sys
INFO=re.compile(r"^info depth (\d+) .*?score (cp|mate) (-?\d+)")
PC="/home/ubuntu/pcbuild/forge"
FENS=[l.strip() for l in open("fresh20f.fens") if l.strip()]
def go(optfile, fen, depth=14):
    opts=[l.strip() for l in open(optfile) if l.strip() and not l.startswith("#")]
    p=subprocess.Popen([PC],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,bufsize=1)
    p.stdin.write("uci\n");p.stdin.flush()
    names=set()
    while True:
        l=p.stdout.readline()
        if not l: raise RuntimeError("died")
        s=l.strip()
        if s.startswith("option name "): names.add(s.split("option name ")[1].split(" type ")[0])
        if s=="uciok": break
    for line in opts:
        nm=line.split("name ")[1].split(" value ")[0]
        if nm not in names: raise RuntimeError("STOP "+nm+" in "+optfile)
        p.stdin.write(line+"\n");p.stdin.flush()
        p.stdin.write("isready\n");p.stdin.flush()
        while p.stdout.readline().strip()!="readyok": pass
    p.stdin.write("ucinewgame\n");p.stdin.flush()
    p.stdin.write("position fen "+fen+"\n");p.stdin.flush()
    p.stdin.write("isready\n");p.stdin.flush()
    while p.stdout.readline().strip()!="readyok": pass
    p.stdin.write("go depth %d\n"%depth);p.stdin.flush()
    last=None; bm=None
    while True:
        l=p.stdout.readline()
        if not l: break
        s=l.strip()
        m=INFO.match(s)
        if m: last=(m.group(2),int(m.group(3)))
        if s.startswith("bestmove"): bm=s.split()[1]; break
    p.stdin.write("quit\n");p.stdin.flush()
    try: p.wait(timeout=10)
    except: p.kill()
    return last,bm
print("| # | position | A: S14 | B: PC20 | C: S14+CorrHist | A==B? | A==C? |")
print("|---|---|---|---|---|---|---|")
ab=0; ac=0; diff=[]
for i,fen in enumerate(FENS,1):
    a=go("A_s14.txt",fen); b=go("B_pc20.txt",fen); c=go("C_corr.txt",fen)
    same_ab = a[1]==b[1]; same_ac = a[1]==c[1]
    ab += not same_ab; ac += not same_ac
    if not same_ab: diff.append((fen,a,b,c))
    print("| %d | %s | %s (%s%d) | %s (%s%d) | %s (%s%d) | %s | %s |"%(
        i,fen[:26],a[1],a[0][0],a[0][1],b[1],b[0][0],b[0][1],c[1],c[0][0],c[0][1],
        "yes" if same_ab else "**NO**","yes" if same_ac else "**NO**"))
print()
print("P1  B differs from A on %d of %d positions"%(ab,len(FENS)))
print("    A vs C differ on %d of %d"%(ac,len(FENS)))
for fen,a,b,c in diff:
    print("   DIFF %s : A %s (%s%d) | B %s (%s%d) | C %s (%s%d)"%(fen[:34],a[1],a[0][0],a[0][1],
          b[1],b[0][0],b[0][1],c[1],c[0][0],c[0][1]))
