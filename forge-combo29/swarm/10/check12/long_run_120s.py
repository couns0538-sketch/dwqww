"""Run the hanging case for 120 s, sampling nodes to see whether the search advances."""
import subprocess,os,threading,json,time
PC=os.path.expanduser("~/builds/pc/forge")
S14=[("LmrQuietBase","93"),("LmrQuietDivisor","205"),("LmrNoisyBase","13"),("LmrNoisyDivisor","333"),
     ("LmrHistoryDivisor","5643"),("NullMoveBase","5"),("LmpBase","8"),("HistoryPruneMultiplier","2220"),
     ("HistoryBonusQuadratic","24"),("HistoryBonusLinear","54"),("HistoryBonusMax","2212"),
     ("SingularDepth","6"),("IirDepth","2"),("NonPawnCorrection","true")]
PC20=S14+[("CuckooRep","true"),("HistRework","2"),("TtPruneV2","true"),("CorrHistV2","true"),
          ("MateAlphaGuard","true"),("OwnBook","false")]
FEN="5k2/8/8/8/8/8/8/1K1Q4 w - - 80 1"
lines=["uci","isready","setoption name Threads value 1","setoption name Hash value 16"]
lines+=["setoption name %s value %s"%kv for kv in PC20]
lines+=["isready","ucinewgame","isready","position fen "+FEN,"isready","go depth 22"]
p=subprocess.Popen([PC],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True,bufsize=1)
for l in lines: p.stdin.write(l+"\n"); p.stdin.flush()
samples=[]
st={"done":False,"best":None,"last":None,"lastdepth":None,"lastnodes":None}
def rd():
    while True:
        line=p.stdout.readline()
        if not line: break
        s=line.rstrip()
        if s.startswith("info depth"):
            import re
            m=re.match(r"info depth (\d+).*? nodes (\d+)",s)
            if m:
                st["lastdepth"]=int(m.group(1)); st["lastnodes"]=int(m.group(2))
            st["last"]=s
        if s.startswith("bestmove"):
            st["best"]=s; st["done"]=True; break
t=threading.Thread(target=rd,daemon=True); t.start()
t0=time.monotonic()
while time.monotonic()-t0 < 120:
    time.sleep(5)
    samples.append({"t":round(time.monotonic()-t0,0),"depth":st["lastdepth"],"nodes":st["lastnodes"],"done":st["done"]})
    print("t=%3.0fs depth %-3s nodes %-10s done %s"%(samples[-1]["t"],st["lastdepth"],st["lastnodes"],st["done"]),flush=True)
    if st["done"]: break
p.kill()
json.dump({"fen":FEN,"samples":samples,"finished":st["done"],"best":st["best"],
           "last_info":st["last"]},open('/agent/repos/dwqww/forge-combo29/swarm/10/check12/raw/long_run_120s.json','w'),indent=1)
