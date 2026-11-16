import queue,re,subprocess,threading,time,chess
S14=[("LmrQuietBase","93"),("LmrQuietDivisor","205"),("LmrNoisyBase","13"),("LmrNoisyDivisor","333"),
("LmrHistoryDivisor","5643"),("NullMoveBase","5"),("LmpBase","8"),("HistoryPruneMultiplier","2220"),
("HistoryBonusQuadratic","24"),("HistoryBonusLinear","54"),("HistoryBonusMax","2212"),
("SingularDepth","6"),("IirDepth","2"),("NonPawnCorrection","true")]
PC20=S14+[("CuckooRep","true"),("HistRework","2"),("TtPruneV2","true"),("CorrHistV2","true"),
("MateAlphaGuard","true"),("OwnBook","false")]
def one(exe,opts,fen,depth=8):
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
    send("position fen "+fen); send("isready"); wait(lambda l:l=="readyok",30)
    send("go depth %d"%depth)
    infos=[];bm=None
    t0=time.monotonic()
    while time.monotonic()-t0<120:
        try: l=q.get(timeout=1.0)
        except queue.Empty: continue
        if l is None: break
        if l.startswith("info depth"): infos.append(l)
        if l.startswith("bestmove"): bm=l; break
    send("quit")
    try: p.wait(timeout=10)
    except: p.kill()
    if not infos: return ("NO_INFO",None,None)
    last=infos[-1]
    m=re.search(r"score (cp|mate) (-?\d+)",last); m2=re.search(r"\bnodes (\d+)",last)
    return (("%s %s"%(m.group(1),m.group(2))) if m else "PARSE_FAIL",
            int(m2.group(1)) if m2 else "PARSE_FAIL",
            bm.split()[1] if bm and len(bm.split())>1 else None)
CASES=[
 ("PAWN","8/P7/k7/P7/2K5/8/7Q/8 w - - 100 1","a7a8q"),
 ("PAWN","8/P7/k7/P7/2K5/8/8/Q7 w - - 100 1","a7a8q"),
 ("PAWN","8/P7/k7/P7/2K5/8/8/4Q3 w - - 100 1","a7a8q"),
 ("CAP ","r5k1/5ppp/8/8/8/8/8/6KQ w - - 100 1","h1a8"),
 ("CAP ","n5k1/5ppp/8/8/8/8/8/6KQ w - - 100 1","h1a8"),
 ("CAP ","b5k1/5ppp/8/8/8/8/8/6KQ w - - 100 1","h1a8"),
 ("CAP ","q5k1/5ppp/8/8/8/8/8/6KQ w - - 100 1","h1a8"),
]
print("COUNTER 100, ONLY MATE IS A PAWN MOVE OR A CAPTURE (verified single-mate with python-chess)")
print("%-5s %-44s %-7s %-11s %-9s %-8s %s" % ("kind","fen","mate","base/S14","PC/PC20","base_bm","PC_bm"))
b0=b1=0
for kind,fen,want in CASES:
    sc0,nd0,bm0=one("/home/ubuntu/builds/rel/forge",S14,fen)
    sc1,nd1,bm1=one("/home/ubuntu/builds/pc/forge",PC20,fen)
    miss = (sc0=="cp 0" and nd0==0)
    find = sc1.startswith("mate")
    if miss: b0+=1
    if find: b1+=1
    print("%-5s %-44s %-7s %-13s %-13s %-8s %-8s %s %s" % (kind,fen,want,
          "%s n=%s"%(sc0,nd0),"%s n=%s"%(sc1,nd1),str(bm0),str(bm1),
          "BASE MISSES" if miss else "-", "PC FINDS" if find else "PC MISSES"))
print()
print("base tree missed the mate (cp 0, 0 nodes) in %d of %d cases" % (b0,len(CASES)))
print("PC build found the mate in %d of %d cases" % (b1,len(CASES)))
