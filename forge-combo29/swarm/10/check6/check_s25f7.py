#!/usr/bin/env python3
"""check_s25f7.py OUTDIR -- seat 10's OWN harness for seat 25's S-F7 and S-F6, both builds, Threads 1.
S-F7: on a TERMINAL root `go nodes 100` / `go movetime 50` emit MANY info lines at 0 nodes, where
      `go depth 5` emits 5. Test whether the count is the DEPTH CAP (my P6) rather than a constant.
S-F6: a checkmated root reports `score mate 0`, a stalemated root `score cp 0`.
Every answer is read to `bestmove` (EOF-safe), one `go` per fresh process."""
import json, os, subprocess, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "audit"))
BASE=os.path.expanduser("~/builds/release/forge"); PC=os.path.expanduser("~/builds/pc/forge")
OUT=os.path.abspath(sys.argv[1]); os.makedirs(OUT,exist_ok=True)
S14=[("LmrQuietBase","93"),("LmrQuietDivisor","205"),("LmrNoisyBase","13"),("LmrNoisyDivisor","333"),
     ("LmrHistoryDivisor","5643"),("NullMoveBase","5"),("LmpBase","8"),("HistoryPruneMultiplier","2220"),
     ("HistoryBonusQuadratic","24"),("HistoryBonusLinear","54"),("HistoryBonusMax","2212"),
     ("SingularDepth","6"),("IirDepth","2"),("NonPawnCorrection","true")]
PC20=S14+[("CuckooRep","true"),("HistRework","2"),("TtPruneV2","true"),("CorrHistV2","true"),
          ("MateAlphaGuard","true"),("OwnBook","false")]
MATE="7k/5Q2/6K1/8/8/8/8/8 b - - 0 1"      # checkmated
STALE="7k/5Q2/5K2/8/8/8/8/8 b - - 0 1"     # stalemated
def one(exe,regime,fen,cmd):
    lines=["uci","isready","setoption name Threads value 1","setoption name Hash value 16"]
    lines+=["setoption name %s value %s"%kv for kv in (S14 if regime=="s14" else PC20)]
    lines+=["isready","ucinewgame","isready","position fen "+fen,"isready",cmd]
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
    depths=[]
    for l in info:
        try: depths.append(int(l.split("depth ")[1].split()[0]))
        except Exception: pass
    nodes=[]
    for l in info:
        if " nodes " in l:
            try: nodes.append(int(l.split(" nodes ")[1].split()[0]))
            except Exception: pass
    sc=None
    for l in reversed(info):
        if " score cp " in l: sc="cp "+l.split(" score cp ")[1].split()[0]; break
        if " score mate " in l: sc="mate "+l.split(" score mate ")[1].split()[0]; break
    bm=[l.split()[1] for l in out if l.startswith("bestmove")]
    return {"info_lines":len(info),"depths_min":min(depths) if depths else None,
            "depths_max":max(depths) if depths else None,"nodes_all_zero":(all(n==0 for n in nodes) if nodes else None),
            "nodes_count":len(nodes),"score":sc,"bestmove":bm[0] if bm else None}
res={}
for bname,exe,reg in (("base_s14",BASE,"s14"),("pc20",PC,"pc20")):
    res[bname]={}
    for label,fen in (("checkmated",MATE),("stalemated",STALE)):
        res[bname][label]={}
        for cmd in ("go depth 5","go nodes 100","go movetime 50","go depth 64","go depth 70"):
            res[bname][label][cmd]=one(exe,reg,fen,cmd)
            print(bname,label,cmd,res[bname][label][cmd],flush=True)
json.dump(res,open(os.path.join(OUT,"check_s25f7.json"),"w"),indent=2)
