import queue,re,subprocess,threading,time
S14=[("LmrQuietBase","93"),("LmrQuietDivisor","205"),("LmrNoisyBase","13"),("LmrNoisyDivisor","333"),
("LmrHistoryDivisor","5643"),("NullMoveBase","5"),("LmpBase","8"),("HistoryPruneMultiplier","2220"),
("HistoryBonusQuadratic","24"),("HistoryBonusLinear","54"),("HistoryBonusMax","2212"),
("SingularDepth","6"),("IirDepth","2"),("NonPawnCorrection","true")]
PC20=S14+[("CuckooRep","true"),("HistRework","2"),("TtPruneV2","true"),("CorrHistV2","true"),
("MateAlphaGuard","true"),("OwnBook","false")]
def one(exe,opts,poscmd,depth):
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
    for k,v in opts: send("setoption name %s value %s"%(k,v))
    send("isready"); wait(lambda l:l=="readyok",30)
    send("ucinewgame"); send("isready"); wait(lambda l:l=="readyok",30)
    send(poscmd); send("isready"); wait(lambda l:l=="readyok",30)
    send("go depth %d"%depth)
    infos=[];bm=None
    t0=time.monotonic()
    while time.monotonic()-t0<200:
        try: l=q.get(timeout=1.0)
        except queue.Empty: continue
        if l is None: break
        if l.startswith("info depth"): infos.append(l)
        if l.startswith("bestmove"): bm=l; break
    send("quit")
    try: p.wait(timeout=10)
    except: p.kill()
    if not infos: return ("NO_INFO_LINE",None,None)
    last=infos[-1]
    m=re.search(r"score (cp|mate) (-?\d+)",last)
    m2=re.search(r"\bnodes (\d+)",last)
    return (("%s %s"%(m.group(1),m.group(2))) if m else "PARSE_FAIL",
            int(m2.group(1)) if m2 else "PARSE_FAIL",
            bm.split()[1] if bm and len(bm.split())>1 else None)
FEN='8/P7/k7/P7/2K5/8/7Q/8 w - - 100 1'
print("board: %s  (the ONLY mate is a7a8q, a PAWN move that resets the halfmove clock)" % FEN)
for name,exe,opts in (("base/S14","/home/ubuntu/builds/rel/forge",S14),
                      ("PC/PC20","/home/ubuntu/builds/pc/forge",PC20)):
    sc,nd,bm=one(exe,opts,"position fen "+FEN,8)
    print("%-10s score=%-10s nodes=%-8s bestmove=%s" % (name,sc,nd,bm))
print()
print("file 6's rule: the mating move is a pawn move, so it resets the counter and the mate")
print("lands at half-move 0 -- BEFORE half-move 100. The mate is reachable, so it MUST be found.")
print("A build that scores this cp 0 with 0 nodes has a REAL defect under file 6.")
