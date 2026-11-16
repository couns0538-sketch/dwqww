import subprocess, json, sys, os
BASE=os.path.expanduser("~/builds/release/forge")
S14=["setoption name %s value %s"%kv for kv in [("LmrQuietBase","93"),("LmrQuietDivisor","205"),("LmrNoisyBase","13"),("LmrNoisyDivisor","333"),("LmrHistoryDivisor","5643"),("NullMoveBase","5"),("LmpBase","8"),("HistoryPruneMultiplier","2220"),("HistoryBonusQuadratic","24"),("HistoryBonusLinear","54"),("HistoryBonusMax","2212"),("SingularDepth","6"),("IirDepth","2"),("NonPawnCorrection","true")]]
def run(delay_ms):
    """send go, wait delay, then send quit; capture everything"""
    import time
    p=subprocess.Popen([BASE],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True,bufsize=1)
    for l in ["uci","isready","setoption name Threads value 1","setoption name Hash value 16"]+S14+["isready","ucinewgame","isready","position startpos"]:
        p.stdin.write(l+"\n"); p.stdin.flush()
    p.stdin.write("go depth 12\n"); p.stdin.flush()
    time.sleep(delay_ms/1000.0)
    try:
        p.stdin.write("quit\n"); p.stdin.flush()
    except Exception: pass
    out=[]
    try:
        out=p.communicate(timeout=60)[0].splitlines()
    except Exception:
        p.kill(); out=p.communicate()[0].splitlines()
    info=[l for l in out if l.startswith("info depth")]
    bm=[l.split()[1] for l in out if l.startswith("bestmove")]
    sc=None
    for l in reversed(info):
        if " score cp " in l: sc="cp "+l.split(" score cp ")[1].split()[0]; break
        if " score mate " in l: sc="mate "+l.split(" score mate ")[1].split()[0]; break
    return {"delay_ms":delay_ms,"info_lines":len(info),"bestmove":bm[0] if bm else None,"last_score":sc}
res=[run(d) for d in (1,2,5,10,20,30,40,60,200)]
print(json.dumps(res,indent=1))
