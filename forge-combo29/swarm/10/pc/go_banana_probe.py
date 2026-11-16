import sys, subprocess, time, os
def probe(exe, settings):
    """hold stdin open, send 'go banana', watch for info depth lines and whether it ever stops"""
    lines=["uci","isready","setoption name Threads value 1","setoption name Hash value 16"]
    lines+=settings+["isready","ucinewgame","isready","position startpos","go banana"]
    p=subprocess.Popen([exe],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,bufsize=1)
    for l in lines: p.stdin.write(l+"\n"); p.stdin.flush()
    time.sleep(2.0)
    p.stdin.write("stop\n"); p.stdin.flush()
    time.sleep(1.0)
    p.stdin.write("quit\n")
    try: p.stdin.flush()
    except Exception: pass
    try: out,_=p.communicate(timeout=20)
    except Exception:
        p.kill(); out,_=p.communicate()
    depth=[l for l in out.splitlines() if l.startswith("info depth")]
    bm=[l for l in out.splitlines() if l.startswith("bestmove")]
    return {"info_depth_lines":len(depth),"last_info":depth[-1] if depth else None,"bestmove":bm}
S14=["setoption name %s value %s"%kv for kv in [("LmrQuietBase","93"),("LmrQuietDivisor","205"),("LmrNoisyBase","13"),("LmrNoisyDivisor","333"),("LmrHistoryDivisor","5643"),("NullMoveBase","5"),("LmpBase","8"),("HistoryPruneMultiplier","2220"),("HistoryBonusQuadratic","24"),("HistoryBonusLinear","54"),("HistoryBonusMax","2212"),("SingularDepth","6"),("IirDepth","2"),("NonPawnCorrection","true")]]
PC20=S14+["setoption name %s value %s"%kv for kv in [("CuckooRep","true"),("HistRework","2"),("TtPruneV2","true"),("CorrHistV2","true"),("MateAlphaGuard","true"),("OwnBook","false")]]
import json
r={"base_s14":probe('/home/ubuntu/builds/release/forge',S14),"pc20":probe('/home/ubuntu/builds/pc/forge',PC20),
   "base_none":probe('/home/ubuntu/builds/release/forge',[])}
print(json.dumps(r,indent=2)[:1400])
