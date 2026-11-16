import subprocess,os,threading,json,time
PC=os.path.expanduser("~/builds/pc/forge")
S14=[("LmrQuietBase","93"),("LmrQuietDivisor","205"),("LmrNoisyBase","13"),("LmrNoisyDivisor","333"),("LmrHistoryDivisor","5643"),("NullMoveBase","5"),("LmpBase","8"),("HistoryPruneMultiplier","2220"),("HistoryBonusQuadratic","24"),("HistoryBonusLinear","54"),("HistoryBonusMax","2212"),("SingularDepth","6"),("IirDepth","2"),("NonPawnCorrection","true")]
PC20=S14+[("CuckooRep","true"),("HistRework","2"),("TtPruneV2","true"),("CorrHistV2","true"),("MateAlphaGuard","true"),("OwnBook","false")]
def run(fen,go,cap=40):
    lines=["uci","isready","setoption name Threads value 1","setoption name Hash value 16"]
    lines+=["setoption name %s value %s"%kv for kv in PC20]
    lines+=["isready","ucinewgame","isready","position fen "+fen,"isready",go]
    p=subprocess.Popen([PC],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True,bufsize=1)
    for l in lines: p.stdin.write(l+"\n"); p.stdin.flush()
    st={"done":False,"best":None,"last":None}
    t0=time.monotonic()
    def rd():
        while True:
            line=p.stdout.readline()
            if not line: break
            s=line.rstrip()
            if s.startswith("info depth"): st["last"]=s
            if s.startswith("bestmove"): st["best"]=s; st["done"]=True; break
    t=threading.Thread(target=rd,daemon=True); t.start()
    t.join(cap)
    el=time.monotonic()-t0
    p.kill()
    return {"state":"DONE" if st["done"] else "HUNG","elapsed_s":round(el,1),"best":st["best"],
            "last":(st["last"][:110] if st["last"] else None)}
fen="5k2/8/8/8/8/8/8/1K1Q4 w - - 80 1"
out={}
for go in ("go depth 22","go wtime 10000 btime 10000","go wtime 6000 btime 6000",
           "go movetime 3000","go nodes 500000","go softnodes 20000"):
    r=run(fen,go)
    out[go]=r
    print("%-28s %-5s %5.1fs  %s"%(go,r["state"],r["elapsed_s"],r["best"] or ""),flush=True)
json.dump(out,open('/agent/repos/dwqww/forge-combo29/swarm/10/check12/raw/clock_vs_depth.json','w'),indent=1)
