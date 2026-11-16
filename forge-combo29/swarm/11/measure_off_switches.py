#!/usr/bin/env python3
"""measure_off_switches.py — the two switches shipped OFF: measure them ON vs OFF.
BARE_KING_ONE_THREAD: a lone-king ending should behave differently with Threads>1... but the
thread rule says Threads 1. So I ALSO report that at Threads 1 this switch cannot matter by
construction, and measure at Threads 2 only to show the switch is live (labelled provisional).
ABORT_PUBLISH: an aborted search (stop mid-search) should publish a bestmove; probe that."""
import os,re,sys,time
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from ucio import Engine
from pc20 import PC20_LINES
SHIPPED="/tmp/pcbuild/forge"; ALLON="/tmp/pconbuild/forge"
class ME(Exception): pass
def opts(threads=1):
    return [l.replace("Threads value 1", f"Threads value {threads}") for l in PC20_LINES]
def search(exe,fen,go="go depth 10",threads=1):
    e=Engine(exe,options=opts(threads),timeout=300); e.start()
    try:
        _,r=e.position(fen=fen)
        if r: raise ME(f"refused {r}")
        infos,bm,_=e.go(go)
        if bm is None: raise ME("no bestmove")
        nodes=None
        for l in infos:
            m=re.search(r"nodes (\d+)",l)
            if m: nodes=int(m.group(1))
        return bm,nodes
    finally: e.quit()
# lone king ending, KQ vs K (a bare-king ending)
LK="6k1/8/8/8/8/8/8/4QK2 w - - 0 1"
print("=== BARE_KING_ONE_THREAD (shipped OFF) ===")
for th in (1,2):
    a=search(SHIPPED,LK,threads=th); b=search(ALLON,LK,threads=th)
    tag=" (provisional: Threads>1)" if th>1 else " (rule-compliant)"
    print(f"  Threads {th}{tag}: shipped={a}  all-on={b}  CHANGED={a!=b}")

# ABORT_PUBLISH: stop mid-search; does a bestmove arrive?
import queue,subprocess,threading
def abort_test(exe,depth=24,delay=0.4):
    p=subprocess.Popen([exe],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True,bufsize=1)
    q=queue.Queue()
    threading.Thread(target=lambda:[q.put(l.rstrip("\n")) for l in iter(p.stdout.readline,"")],daemon=True).start()
    p.stdin.write("uci\n"); p.stdin.flush()
    while q.get(timeout=10).strip()!="uciok": pass
    for line in opts(1): p.stdin.write(line+"\n")
    p.stdin.write("isready\n"); p.stdin.flush()
    while q.get(timeout=10).strip()!="readyok": pass
    p.stdin.write("position startpos\nisready\ngo depth 24\n"); p.stdin.flush()
    time.sleep(delay)
    p.stdin.write("stop\n"); p.stdin.flush()
    t0=time.monotonic(); bm=None
    while time.monotonic()-t0<8:
        try: l=q.get(timeout=0.2)
        except queue.Empty: continue
        if l.startswith("bestmove"): bm=l.split()[1]; break
    try: p.stdin.write("quit\n"); p.stdin.flush(); p.wait(timeout=5)
    except Exception: p.kill()
    return bm
print("\n=== ABORT_PUBLISH (shipped OFF) ===")
for exe,name in ((SHIPPED,"shipped"),(ALLON,"all-on")):
    bm=abort_test(exe)
    print(f"  {name:8} stop mid-search -> bestmove={bm}")
