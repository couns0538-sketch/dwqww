import subprocess, time, re, statistics
EXE="/home/ubuntu/pcbuild/forge"
OPT="../job7/pc20_opts.txt"
FEN="5R2/1p5k/6p1/8/1K6/5q2/8/8 b - - 0 1"
INFO=re.compile(r"^info depth (\d+) .*?score (cp|mate) (-?\d+).*?nodes (\d+)")
def run():
    p=subprocess.Popen([EXE],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,bufsize=1)
    p.stdin.write("uci\n");p.stdin.flush()
    names=set()
    while True:
        l=p.stdout.readline()
        if not l: raise RuntimeError("died")
        s=l.strip()
        if s.startswith("option name "): names.add(s.split("option name ")[1].split(" type ")[0])
        if s=="uciok": break
    for line in [x.strip() for x in open(OPT) if x.strip() and not x.startswith("#")]:
        nm=line.split("name ")[1].split(" value ")[0]
        if nm not in names: raise RuntimeError("STOP option "+nm)
        p.stdin.write(line+"\n");p.stdin.flush()
        p.stdin.write("isready\n");p.stdin.flush()
        while p.stdout.readline().strip()!="readyok": pass
    p.stdin.write("ucinewgame\n");p.stdin.flush()
    p.stdin.write("position fen "+FEN+"\n");p.stdin.flush()
    p.stdin.write("isready\n");p.stdin.flush()
    while p.stdout.readline().strip()!="readyok": pass
    t=time.monotonic(); p.stdin.write("go depth 12\n");p.stdin.flush()
    last=None; bm=None
    while True:
        l=p.stdout.readline()
        if not l: raise RuntimeError("died in search")
        s=l.strip()
        m=INFO.match(s)
        if m: last=(m.group(2),int(m.group(3)),int(m.group(4)))
        if s.startswith("bestmove"): bm=s.split()[1]; break
    w=time.monotonic()-t
    p.stdin.write("quit\n");p.stdin.flush()
    try: p.wait(timeout=10)
    except: p.kill()
    return bm, last, w
print("PC r15 + PC20, Threads 1 (no Threads option sent), depth 12, FEN", FEN)
print("| run | bestmove | score | nodes | wall s |")
print("|---|---|---|---|---|")
res=[]
for i in range(6):
    bm,last,w=run(); res.append((bm,last,w))
    print("| %d | %s | %s %d | %d | %.3f |"%(i+1,bm,last[0],last[1],last[2],w))
moves={r[0] for r in res}; nodes={r[1][2] for r in res}; scores={r[1][0]+" "+str(r[1][1]) for r in res}
print()
print("distinct bestmoves:",len(moves),moves)
print("distinct node counts:",len(nodes),sorted(nodes))
print("distinct scores:",len(scores),scores)
print("wall min/max: %.3f / %.3f s"%(min(r[2] for r in res),max(r[2] for r in res)))
