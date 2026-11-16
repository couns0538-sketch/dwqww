import sys,os,json,subprocess,re
PC=os.path.expanduser("~/builds/pc/forge")
S14=[("LmrQuietBase","93"),("LmrQuietDivisor","205"),("LmrNoisyBase","13"),("LmrNoisyDivisor","333"),("LmrHistoryDivisor","5643"),("NullMoveBase","5"),("LmpBase","8"),("HistoryPruneMultiplier","2220"),("HistoryBonusQuadratic","24"),("HistoryBonusLinear","54"),("HistoryBonusMax","2212"),("SingularDepth","6"),("IirDepth","2"),("NonPawnCorrection","true")]
PC20=S14+[("CuckooRep","true"),("HistRework","2"),("TtPruneV2","true"),("CorrHistV2","true"),("MateAlphaGuard","true"),("OwnBook","false")]
def one(go,pos="position startpos"):
    lines=["uci","isready","setoption name Threads value 1","setoption name Hash value 16"]
    lines+=["setoption name %s value %s"%kv for kv in PC20]
    lines+=["isready","ucinewgame","isready",pos,"isready",go]
    p=subprocess.Popen([PC],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True,bufsize=1)
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
    try: p.wait(timeout=120)
    except Exception: p.kill()
    pd=[]
    for l in out:
        m=re.match(r"info depth (\d+) .*? nodes (\d+)",l)
        if m: pd.append((int(m.group(1)),int(m.group(2))))
    last=[l for l in out if l.startswith("info depth")]
    last=last[-1] if last else ""
    n=None
    if " nodes " in last:
        try: n=int(last.split(" nodes ")[1].split()[0])
        except Exception: pass
    return {"go":go,"depths":pd,"last_nodes":n,"last_depth":pd[-1][0] if pd else None,
            "prev_nodes":pd[-2][1] if len(pd)>1 else None,
            "info_lines":len(pd),
            "bestmove":next((l.split()[1] for l in out if l.startswith("bestmove")),None)}
res={}
for n in (2000,20000,50000,250000):
    a=one("go nodes %d"%n); b=one("go softnodes %d"%n)
    res["N%d"%n]={"nodes":{"depth":a["last_depth"],"last_nodes":a["last_nodes"],"depths":a["depths"],"bestmove":a["bestmove"]},
                  "softnodes":{"depth":b["last_depth"],"last_nodes":b["last_nodes"],"depths":b["depths"],"bestmove":b["bestmove"]}}
    print("N=%-7d go nodes: last depth %-3s nodes %-8s | softnodes: last depth %-3s nodes %-8s"%(
        n,a["last_depth"],a["last_nodes"],b["last_depth"],b["last_nodes"]))
json.dump(res,open('/agent/repos/dwqww/forge-combo29/swarm/10/check10/raw/nodes_vs_softnodes.json','w'),indent=1)
