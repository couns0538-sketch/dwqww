#!/usr/bin/env python3
"""k5_direct.py -- K5 with stderr CAPTURED (my Drv sent stderr to DEVNULL, which made "0 reports"
unmeasurable -- a "not shown", not a "0"). This runs the engine directly with subprocess, sending
ucinewgame/position FIRST and the go LAST, then reading stdout to bestmove and reading stderr after,
so the EOF-abort trap cannot fire (the search finishes before the process is closed)."""
import json,os,subprocess,sys,threading
EXE=os.path.expanduser("~/builds/tsan/forge")
PLANTED=os.path.expanduser("~/builds/planted_tsan/forge")
OUT=os.path.abspath(sys.argv[1]); SETS=os.path.join(OUT,"sets"); os.makedirs(os.path.join(OUT,"K5"),exist_ok=True)
S14=[("LmrQuietBase","93"),("LmrQuietDivisor","205"),("LmrNoisyBase","13"),("LmrNoisyDivisor","333"),
     ("LmrHistoryDivisor","5643"),("NullMoveBase","5"),("LmpBase","8"),("HistoryPruneMultiplier","2220"),
     ("HistoryBonusQuadratic","24"),("HistoryBonusLinear","54"),("HistoryBonusMax","2212"),
     ("SingularDepth","6"),("IirDepth","2"),("NonPawnCorrection","true")]
MARK=("WARNING: ThreadSanitizer","ThreadSanitizer: data race")
def nm(exe):
    return subprocess.run(["nm","-C",exe],capture_output=True,text=True).stdout.count("__tsan_")
def one(exe,fen,threads,timeout=300):
    env={k:v for k,v in os.environ.items() if k not in ("TSAN_OPTIONS","ASAN_OPTIONS","UBSAN_OPTIONS")}
    lines=["uci","isready","setoption name Threads value %d"%threads,"setoption name Hash value 16"]
    lines+=["setoption name %s value %s"%kv for kv in S14]
    lines+=["isready","ucinewgame","isready","position fen "+fen,"isready","go depth 12"]
    p=subprocess.Popen([exe],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,bufsize=1,env=env)
    for l in lines:
        p.stdin.write(l+"\n"); p.stdin.flush()
    out=[]
    try:
        while True:
            line=p.stdout.readline()
            if not line: break
            out.append(line.rstrip())
            if line.startswith("bestmove"): break
    except Exception: pass
    try:
        p.stdin.write("quit\n"); p.stdin.flush()
    except Exception: pass
    err=""
    try:
        p.wait(timeout=timeout); err=p.stderr.read()
    except Exception:
        p.kill()
    nodes=None
    for l in out:
        if l.startswith("info") and " nodes " in l:
            try: nodes=int(l.split(" nodes ")[1].split()[0])
            except Exception: pass
    best=next((l.split()[1] for l in out if l.startswith("bestmove")),"NONE")
    return {"fen":fen,"threads":threads,"nodes":nodes,"bestmove":best,
            "tsan":sum(err.count(m) for m in MARK),"stderr_bytes":len(err),"rc":p.returncode}
meta={"real_exe":EXE,"real_nm_tsan":nm(EXE),"planted_exe":PLANTED,"planted_nm_tsan":nm(PLANTED),
      "TSAN_OPTIONS":os.environ.get("TSAN_OPTIONS","unset"),"stderr":"CAPTURED"}
json.dump(meta,open(os.path.join(OUT,"K5","meta_direct.json"),"w"),indent=2)
fens=[l.strip() for l in open(os.path.join(SETS,"first200.fens")) if l.strip()][:50]
proof=one(PLANTED,fens[0],4)
json.dump(proof,open(os.path.join(OUT,"K5","proof_planted_direct.json"),"w"),indent=2)
print("PROOF planted:",{k:proof[k] for k in ("tsan","nodes","bestmove","rc","stderr_bytes")},flush=True)
res={}
for t in (2,4):
    rows=[one(EXE,f,t) for f in fens]
    res["T%d"%t]={"searches":len(rows),"tsan_reports":sum(r["tsan"] for r in rows),
                  "with_report":sum(1 for r in rows if r["tsan"]>0),
                  "null_nodes":sum(1 for r in rows if r["nodes"] is None),
                  "bad_rc":sum(1 for r in rows if r["rc"] not in (0,)),
                  "rows":rows}
    json.dump(res["T%d"%t],open(os.path.join(OUT,"K5","sweep_direct_T%d.json"%t),"w"),indent=1)
    print(" T%d done reports=%d null_nodes=%d"%(t,res["T%d"%t]["tsan_reports"],res["T%d"%t]["null_nodes"]),flush=True)
s={"proof1_nm_gt_0":meta["real_nm_tsan"]>0 and meta["planted_nm_tsan"]>0,
   "proof2_planted_counted":proof["tsan"]>0,
   "T2_reports":res["T2"]["tsan_reports"],"T4_reports":res["T4"]["tsan_reports"],
   "T2_searches":res["T2"]["searches"],"T4_searches":res["T4"]["searches"],
   "T2_null_nodes":res["T2"]["null_nodes"],"T4_null_nodes":res["T4"]["null_nodes"]}
s["verdict"]=("PASS (0 reports, with both proofs)" if (s["proof1_nm_gt_0"] and s["proof2_planted_counted"]
     and s["T2_reports"]==0 and s["T4_reports"]==0 and s["T2_null_nodes"]==0 and s["T4_null_nodes"]==0)
     else "NOT SHOWN / REFUTED")
json.dump(s,open(os.path.join(OUT,"K5","summary_direct.json"),"w"),indent=2)
print(json.dumps(s,indent=2))
