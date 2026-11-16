import sys,os,json
sys.path.insert(0,'/agent/repos/dwqww/forge-combo29/swarm/10/checks8' if os.path.isdir('/agent/repos/dwqww/forge-combo29/swarm/10/checks8') else '/agent/repos/dwqww/forge-combo29/swarm/10/check8')
sys.path.insert(0,'/agent/repos/dwqww/forge-combo29/swarm/10')
import importlib.util
spec=importlib.util.spec_from_file_location("c8","/agent/repos/dwqww/forge-combo29/swarm/10/check8/check8.py")
# simpler: reimplement the search call here
import subprocess,re
S14=[("LmrQuietBase","93"),("LmrQuietDivisor","205"),("LmrNoisyBase","13"),("LmrNoisyDivisor","333"),("LmrHistoryDivisor","5643"),("NullMoveBase","5"),("LmpBase","8"),("HistoryPruneMultiplier","2220"),("HistoryBonusQuadratic","24"),("HistoryBonusLinear","54"),("HistoryBonusMax","2212"),("SingularDepth","6"),("IirDepth","2"),("NonPawnCorrection","true")]
def one(exe,pos,go,depth_regime="s14"):
    lines=["uci","isready","setoption name Threads value 1","setoption name Hash value 16"]
    lines+=["setoption name %s value %s"%kv for kv in S14]
    lines+=["isready","ucinewgame","isready",pos,"isready",go]
    p=subprocess.Popen([exe],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True,bufsize=1)
    for l in lines: p.stdin.write(l+"\n"); p.stdin.flush()
    out=[]
    while True:
        line=p.stdout.readline()
        if not line: break
        out.append(line.rstrip())
        if line.startswith("bestmove"): break
    p.stdin.write("quit\n")
    try: p.stdin.flush()
    except Exception: pass
    try: p.wait(timeout=60)
    except Exception: p.kill()
    info=[l for l in out if l.startswith("info depth")]
    last=info[-1] if info else ""
    n=re.search(r" nodes (\d+)",last); pv=(" pv " in last)
    sc=re.search(r" score (cp|mate) (-?\d+)",last)
    return {"nodes":int(n.group(1)) if n else None,"pv":len(last.split(" pv ",1)[1].split()) if pv else 0,
            "score":(sc.group(1),int(sc.group(2))) if sc else None}
BOARDS={
 "KR_vs_K":"1K6/8/8/3R4/8/8/8/k7 w - - %d 1",
 "KQ_vs_K":"8/5K2/7Q/4k3/8/8/8/8 w - - %d 1",
 "KBB_vs_K":"8/5K2/7B/4k3/8/8/6B1/8 w - - %d 1",
 "KRP_vs_K":"8/5K2/7R/4k3/8/8/6P1/8 w - - %d 1",
}
rows=[]
for name,fen in BOARDS.items():
    for hm in (98,99,100):
        r=one('/home/ubuntu/builds/release/forge',"position fen "+(fen%hm),"go depth 10")
        r.update({"board":name,"hm":hm}); rows.append(r)
        print("%-9s hm %-3d nodes %-9s pv %-2d score %s"%(name,hm,r["nodes"],r["pv"],r["score"]),flush=True)
json.dump(rows,open('/agent/repos/dwqww/forge-combo29/swarm/10/check8/raw/cp0_threshold.json','w'),indent=1)
# test the proposed threshold: every cp0 record classified correctly?
bad=[r for r in rows if r["score"]==("cp",0) and not ((r["nodes"]==0 and r["pv"]==0) or (r["nodes"] and r["nodes"]>10000))]
print()
print("proposed rule: cp0 with 0 nodes + empty pv = ROOT; cp0 with >10,000 nodes = HORIZON")
print("records violating it:",len(bad),bad)
