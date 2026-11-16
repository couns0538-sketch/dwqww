import argparse,json,os,queue,re,subprocess,threading,time
import chess
S14=[("LmrQuietBase","93"),("LmrQuietDivisor","205"),("LmrNoisyBase","13"),("LmrNoisyDivisor","333"),
("LmrHistoryDivisor","5643"),("NullMoveBase","5"),("LmpBase","8"),("HistoryPruneMultiplier","2220"),
("HistoryBonusQuadratic","24"),("HistoryBonusLinear","54"),("HistoryBonusMax","2212"),
("SingularDepth","6"),("IirDepth","2"),("NonPawnCorrection","true")]
PC20=S14+[("CuckooRep","true"),("HistRework","2"),("TtPruneV2","true"),("CorrHistV2","true"),
("MateAlphaGuard","true"),("OwnBook","false")]
BOARDS=[("startpos","rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"),
("G-mid-1","1r6/2k2pp1/2p2n2/2Pppb1p/7P/1P2PPP1/P3BK2/R1R5 b - - 0 1"),
("G-mid-2","r3r1k1/p1bb1ppp/1p1q4/3P1p2/1nBP4/PPN2N1P/5PP1/1R1Q1RK1 b - - 0 1"),
("G-end-1","8/8/6K1/1kr5/8/8/8/r7 w - - 0 1"),
("G-end-2","k7/6R1/5N2/p4K1P/P7/8/8/8 b - - 0 1")]
def one(exe,fen,go,limit=60):
    p=subprocess.Popen([exe],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True,bufsize=1)
    q=queue.Queue()
    def rd():
        for l in p.stdout: q.put(l.rstrip("\n"))
        q.put(None)
    threading.Thread(target=rd,daemon=True).start()
    def send(c): p.stdin.write(c+"\n"); p.stdin.flush()
    def wait(pred,lim):
        t0=time.monotonic()
        while True:
            rem=lim-(time.monotonic()-t0)
            if rem<=0: return None
            try: l=q.get(timeout=rem)
            except queue.Empty: return None
            if l is None: return None
            if pred(l): return l
    send("uci"); wait(lambda l:l.startswith("uciok"),30)
    send("setoption name Threads value 1"); send("setoption name Hash value 16")
    for k,v in PC20: send("setoption name %s value %s"%(k,v))
    send("isready"); wait(lambda l:l=="readyok",30)
    send("ucinewgame"); send("isready"); wait(lambda l:l=="readyok",30)
    send("position fen "+fen); send("isready"); wait(lambda l:l=="readyok",30)
    t0=time.monotonic(); send("go "+go)
    infos=[];bm=None
    while time.monotonic()-t0<limit:
        try: l=q.get(timeout=0.5)
        except queue.Empty: continue
        if l is None: break
        if l.startswith("info depth"): infos.append(l)
        if l.startswith("bestmove"): bm=l; break
    wall=time.monotonic()-t0
    send("quit")
    try: p.wait(timeout=10)
    except: p.kill()
    last=infos[-1] if infos else None
    sc=nd=None;dep=None
    if last:
        m=re.search(r"score (cp|mate) (-?\d+)",last); sc=("%s %s"%(m.group(1),m.group(2))) if m else "PARSE_FAIL"
        m2=re.search(r"\bnodes (\d+)",last); nd=int(m2.group(1)) if m2 else None
        md=re.match(r"info depth (\d+)",last); dep=int(md.group(1)) if md else None
    return {"score":sc,"nodes":nd,"depth":dep,"wall_ms":int(wall*1000),
            "bestmove":bm.split()[1] if bm and len(bm.split())>1 else None}
ap=argparse.ArgumentParser(); ap.add_argument("exe"); ap.add_argument("--reps",type=int,default=5)
ap.add_argument("--out",default="mt.jsonl"); a=ap.parse_args()
print("exe: %s PC20 Threads 1 reps %d"%(a.exe,a.reps),flush=True)
print("%-9s %-9s %-9s %-8s %-8s %-8s %s"%("board","movetime","wall_ms","pct","nodes","depth","score"),flush=True)
rows=[]
for label,fen in BOARDS:
    for ms in (1000,3000):
        runs=[one(a.exe,fen,"movetime %d"%ms) for _ in range(a.reps)]
        ws=sorted(r["wall_ms"] for r in runs)
        med=ws[len(ws)//2]
        ns=sorted({r["nodes"] for r in runs if r["nodes"]})
        print("%-9s %-9d %-9s %-8s %-8s %-8s %s"%(label,ms,
            "%d-%d"%(ws[0],ws[-1]), "%.0f%%"%(100*med/ms),
            (str(ns[0]) if len(ns)==1 else "%d..%d"%(ns[0],ns[-1]) if ns else "?"),
            runs[0]["depth"], runs[0]["score"]),flush=True)
        rows.append({"board":label,"movetime":ms,"runs":runs,"walls":ws,"med":med})
with open(a.out,"w") as fh:
    for r in rows: fh.write(json.dumps(r)+"\n")
print("\nwrote %s"%a.out,flush=True)
