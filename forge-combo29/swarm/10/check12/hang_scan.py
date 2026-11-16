import subprocess,os,threading,json
PC=os.path.expanduser("~/builds/pc/forge")
S14=[("LmrQuietBase","93"),("LmrQuietDivisor","205"),("LmrNoisyBase","13"),("LmrNoisyDivisor","333"),("LmrHistoryDivisor","5643"),("NullMoveBase","5"),("LmpBase","8"),("HistoryPruneMultiplier","2220"),("HistoryBonusQuadratic","24"),("HistoryBonusLinear","54"),("HistoryBonusMax","2212"),("SingularDepth","6"),("IirDepth","2"),("NonPawnCorrection","true")]
PC20=S14+[("CuckooRep","true"),("HistRework","2"),("TtPruneV2","true"),("CorrHistV2","true"),("MateAlphaGuard","true"),("OwnBook","false")]
def run(fen,cap=25):
    lines=["uci","isready","setoption name Threads value 1","setoption name Hash value 16"]
    lines+=["setoption name %s value %s"%kv for kv in PC20]
    lines+=["isready","ucinewgame","isready","position fen "+fen,"isready","go depth 22"]
    p=subprocess.Popen([PC],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True,bufsize=1)
    for l in lines: p.stdin.write(l+"\n"); p.stdin.flush()
    st={"done":False,"best":None,"last":None}
    def rd():
        while True:
            line=p.stdout.readline()
            if not line: break
            s=line.rstrip()
            if s.startswith("info depth"): st["last"]=s
            if s.startswith("bestmove"): st["best"]=s; st["done"]=True; break
    t=threading.Thread(target=rd,daemon=True); t.start()
    t.join(cap)
    p.kill()
    return ("DONE" if st["done"] else "HUNG", st["last"], st["best"])
base="5k2/8/8/8/8/8/8/1K1Q4 w - - %d 1"
out={}
for c in (0,40,60,70,75,78,79,80,81,82,84,86,87,88,90,99):
    fen=base % c
    r=run(fen)
    out[c]={"state":r[0],"last_info":r[1],"bestmove":r[2]}
    print("counter %-3d -> %-5s %s"%(c,r[0],(r[2] or "")),flush=True)
json.dump(out,open('/agent/repos/dwqww/forge-combo29/swarm/10/check12/raw/hang_scan.json','w'),indent=1)
