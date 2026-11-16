#!/usr/bin/env python3
"""measure_switches.py — measure each FORGE_FIX_* switch's observable effect.
Compares the real PC r15 build (switches at their shipped defaults) against an
all-fixes-flipped-to-0 build, on probes chosen to stress each switch.
Threads 1 everywhere. Any missing parse aborts."""
import os,re,sys,queue,subprocess,threading,time
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import chess
from ucio import Engine
from pc20 import PC20_LINES
ON  = "/tmp/pcbuild/forge"      # shipped PC r15
OFF = "/tmp/pcoffbuild/forge"   # same source, five switches flipped to 0

class ME(Exception): pass

def search(exe,fen,go="go depth 8",opts=None,moves=None):
    e=Engine(exe,options=opts if opts is not None else PC20_LINES,timeout=300); e.start()
    try:
        if moves:
            e.send("position startpos moves "+moves)
        else:
            e.send(f"position fen {fen}")
        e.send("isready"); e.read_until("readyok")
        infos,bm,_=e.go(go)
        if bm is None: raise ME("no bestmove")
        nodes=None
        for l in infos:
            m=re.search(r"nodes (\d+)",l)
            if m: nodes=int(m.group(1))
        return bm,nodes,len(infos)
    finally: e.quit()

def infinite_volunteers(exe,fen,wait=5.0):
    """Does `go infinite` volunteer a bestmove with NO stop sent?"""
    p=subprocess.Popen([exe],stdin=subprocess.PIPE,stdout=subprocess.PIPE,
                       stderr=subprocess.DEVNULL,text=True,bufsize=1)
    q=queue.Queue()
    threading.Thread(target=lambda:[q.put(l.rstrip("\n")) for l in iter(p.stdout.readline,"")],daemon=True).start()
    p.stdin.write("uci\n"); p.stdin.flush()
    while True:
        if q.get(timeout=10).strip()=="uciok": break
    for line in PC20_LINES: p.stdin.write(line+"\n")
    p.stdin.write("isready\n"); p.stdin.flush()
    while q.get(timeout=10).strip()!="readyok": pass
    p.stdin.write(f"position fen {fen}\nisready\ngo infinite\n"); p.stdin.flush()
    t0=time.monotonic(); bm=None
    while time.monotonic()-t0<wait:
        try: l=q.get(timeout=0.2)
        except queue.Empty: continue
        if l.startswith("bestmove"): bm=l.split()[1]; break
    try:
        p.stdin.write("stop\nquit\n"); p.stdin.flush(); p.wait(timeout=5)
    except Exception: p.kill()
    return bm

print(f"ON  = {ON}  (shipped PC r15)\nOFF = {OFF}  (same source, five switches -> 0)\nThreads 1\n")

# 1 ROOT_DRAWN: threefold root
TF="g1f3 g8f6 f3g1 f6g8 g1f3 g8f6 f3g1 f6g8"
try:
    a=search(ON,"",moves=TF); b=search(OFF,"",moves=TF)
    print(f"[ROOT_DRAWN] threefold root  ON={a}  OFF={b}   CHANGED={a!=b}")
    # halfmove 100 mate
    M="6k1/5ppp/8/8/8/8/5PPP/3Q2K1 w - - 100 1"
    a2=search(ON,M,go="go depth 5"); b2=search(OFF,M,go="go depth 5")
    print(f"[ROOT_DRAWN] H=100 mate      ON={a2}  OFF={b2}   CHANGED={a2!=b2}")
except ME as e: print("[ROOT_DRAWN] MEASUREMENT FAILED",e)

# 2 GO_PARSE
try:
    a=search(ON,"",go="go depth nodes 100"); b=search(OFF,"",go="go depth nodes 100")
    print(f"[GO_PARSE]   'go depth nodes 100' ON maxdepth-lines={a[2]} OFF={b[2]}  CHANGED={a!=b}")
except ME as e: print("[GO_PARSE] MEASUREMENT FAILED",e)

# 3 ISREADY_PENDING: isready during a search must not disturb it
try:
    def during(exe):
        e=Engine(exe,options=PC20_LINES,timeout=300); e.start()
        try:
            e.send("position startpos"); e.send("isready"); e.read_until("readyok")
            e.send("go depth 14"); time.sleep(0.25); e.send("isready")
            ans=e.read_until("readyok",timeout=60)
            e.send("isready"); e.read_until("readyok",timeout=60)
            infos,bm,_=e.go("go depth 8")
            return bm
        finally: e.quit()
    a=during(ON); b=during(OFF)
    print(f"[ISREADY]    isready mid-search   ON={a}  OFF={b}   CHANGED={a!=b}")
except Exception as ex: print("[ISREADY] MEASUREMENT FAILED",ex)

# 4 HARD_LIMIT_EMERGENCY: movetime 50 overshoot
try:
    def mtime(exe):
        e=Engine(exe,options=PC20_LINES,timeout=120); e.start()
        try:
            e.send("position fen r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq - 3 3")
            e.send("isready"); e.read_until("readyok")
            t0=time.monotonic(); e.send("go movetime 50"); e.read_until("bestmove",timeout=10)
            return (time.monotonic()-t0)*1000
        finally: e.quit()
    a=[mtime(ON) for _ in range(3)]; b=[mtime(OFF) for _ in range(3)]
    print(f"[HARD_LIMIT] movetime 50 (ms)    ON={['%.1f'%x for x in a]} OFF={['%.1f'%x for x in b]}")
except Exception as ex: print("[HARD_LIMIT] MEASUREMENT FAILED",ex)

# 5 ABORT_PUBLISH: both 0 in shipped build -> nothing to compare
print("[ABORT_PUBLISH] both builds have this switch at 0, so no ON/OFF comparison is possible here")
# 6 BARE_KING_ONE_THREAD: both 0
print("[BARE_KING_ONE_THREAD] both builds have this switch at 0, so no ON/OFF comparison is possible here")
