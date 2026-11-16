#!/usr/bin/env python3
"""file6_test.py EXE FEN_BASE --counter H --depth D

FABLE_TO_swarm_6's test for a high-counter cp 0:
  "the same board with counter 0, go depth 20 or more, read mate N; it is a defect only if
   2N - 1 <= 100 - counter AND the board with the real counter still scores cp 0 at that depth."
Prints both numbers and the inequality. Threads 1, PC20.
"""
import argparse, queue, re, subprocess, threading, time, sys
sys.path.insert(0, '.')
S14 = [("LmrQuietBase","93"),("LmrQuietDivisor","205"),("LmrNoisyBase","13"),("LmrNoisyDivisor","333"),
("LmrHistoryDivisor","5643"),("NullMoveBase","5"),("LmpBase","8"),("HistoryPruneMultiplier","2220"),
("HistoryBonusQuadratic","24"),("HistoryBonusLinear","54"),("HistoryBonusMax","2212"),
("SingularDepth","6"),("IirDepth","2"),("NonPawnCorrection","true")]
PC20 = S14 + [("CuckooRep","true"),("HistRework","2"),("TtPruneV2","true"),("CorrHistV2","true"),
("MateAlphaGuard","true"),("OwnBook","false")]

def one(exe, opts, poscmd, depth, limit=900):
    p=subprocess.Popen([exe],stdin=subprocess.PIPE,stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,text=True,bufsize=1)
    q=queue.Queue()
    def rd():
        for line in p.stdout: q.put(line.rstrip("\n"))
        q.put(None)
    threading.Thread(target=rd,daemon=True).start()
    def send(c): p.stdin.write(c+"\n"); p.stdin.flush()
    def wait(pred,lim):
        t0=time.monotonic()
        while True:
            rem=lim-(time.monotonic()-t0)
            if rem<=0: return "TIMEOUT",None
            try: line=q.get(timeout=rem)
            except queue.Empty: return "TIMEOUT",None
            if line is None: return "EOF",None
            if pred(line): return "OK",line
    send("uci"); wait(lambda l:l.startswith("uciok"),30)
    send("setoption name Threads value 1"); send("setoption name Hash value 16")
    for k,v in opts: send("setoption name %s value %s"%(k,v))
    send("isready"); wait(lambda l:l=="readyok",30)
    send("ucinewgame"); send("isready"); wait(lambda l:l=="readyok",30)
    send(poscmd); send("isready")
    refused=[]
    t0=time.monotonic()
    while time.monotonic()-t0<20:
        try: line=q.get(timeout=0.5)
        except queue.Empty: continue
        if line is None: break
        if any(b in line for b in ("invalid FEN","invalid value","illegal move","unknown option")): refused.append(line)
        if line.strip()=="readyok": break
    if refused:
        try: send("quit"); p.wait(timeout=10)
        except Exception: p.kill()
        return {"refused":refused}
    send("go depth %d"%depth)
    infos=[]; bm=None
    t0=time.monotonic()
    while time.monotonic()-t0<limit:
        try: line=q.get(timeout=1.0)
        except queue.Empty: continue
        if line is None: break
        if line.startswith("info depth"): infos.append(line)
        if line.startswith("bestmove"): bm=line; break
    try: send("quit"); p.wait(timeout=10)
    except Exception: p.kill()
    if not infos: return {"score":"NO_INFO_LINE","depth":None,"bestmove":None}
    last=infos[-1]
    m=re.search(r"score (cp|mate) (-?\d+)",last); md=re.search(r"^info depth (\d+)",last)
    return {"score":("%s %s"%(m.group(1),m.group(2))) if m else "PARSE_FAIL",
            "depth":int(md.group(1)) if md else None,
            "bestmove":bm.split()[1] if bm and len(bm.split())>1 else None}

ap=argparse.ArgumentParser()
ap.add_argument("exe"); ap.add_argument("template")
ap.add_argument("--counter",type=int,required=True); ap.add_argument("--deep",type=int,default=24)
ap.add_argument("--depth",type=int,default=10)
a=ap.parse_args()
print("exe: %s  Threads 1  PC20" % a.exe)
print("board template: %s" % a.template)
print()
print("STEP 1: counter 0, deep search -> mate N")
r0=one(a.exe,PC20,"position fen "+a.template.format(0),a.deep)
print("  counter 0 at go depth %d: %s (reached depth %s)" % (a.deep, r0.get("score"), r0.get("depth")))
n=None
if r0.get("score","").startswith("mate"):
    v=int(r0["score"].split()[1])
    n = v if v>0 else -v
    plies = 2*n-1 if v>0 else 2*n
    left = 100-a.counter
    print("  => mate %+d means %d plies; half-moves left at counter %d: %d"
          % (v, plies, a.counter, left))
    print("  INEQUALITY 2N-1 <= 100-counter : %d <= %d : %s"
          % (plies, left, "TRUE" if plies<=left else "FALSE"))
else:
    print("  => no mate score at depth %d, so no forced mate within the horizon" % a.deep)
print()
print("STEP 2: the real counter at the same depth as the finding")
rH=one(a.exe,PC20,"position fen "+a.template.format(a.counter),a.depth)
print("  counter %d at go depth %d: %s  %s" % (a.counter,a.depth,rH.get("score"),rH.get("bestmove")))
print()
if n is not None:
    ok = (2*n-1 if n>0 else 2*n) <= (100-a.counter) and rH.get("score")=="cp 0"
    print("VERDICT: %s" % ("DEFECT - a forced mate ends by half-move 100 AND the real counter still scores cp 0"
                          if ok else "NOT A DEFECT - the mate is not reachable before half-move 100, or the real counter is not cp 0"))
else:
    print("VERDICT: NOT A DEFECT as far as this test can see - no forced mate found by depth %d" % a.deep)
