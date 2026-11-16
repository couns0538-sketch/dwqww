#!/usr/bin/env python3
"""check_infinite_pc20.py EXE BUILD — does `go infinite` at a TERMINAL root VOLUNTEER bestmove?
Critical: we do NOT send stop before the deadline, so a bestmove within the window is volunteered."""
import os, queue, subprocess, sys, threading, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pc20 import PC20_LINES, describe
EXE=sys.argv[1]; BUILD=sys.argv[2] if len(sys.argv)>2 else "?"
WAIT=6.0
CASES=[("checkmate root","8/8/8/8/8/6K1/8/Q5k1 b - - 0 1"),
       ("stalemate root","7k/5Q2/6K1/8/8/8/8/8 b - - 0 1"),
       ("ordinary board","rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")]
def run(fen):
    p=subprocess.Popen([EXE],stdin=subprocess.PIPE,stdout=subprocess.PIPE,
                       stderr=subprocess.DEVNULL,text=True,bufsize=1)
    q=queue.Queue()
    threading.Thread(target=lambda:[q.put(l.rstrip("\n")) for l in iter(p.stdout.readline,"")],daemon=True).start()
    p.stdin.write("uci\n"); p.stdin.flush()
    while True:
        l=q.get(timeout=10)
        if l.strip()=="uciok": break
    for line in PC20_LINES: p.stdin.write(line+"\n")
    p.stdin.write(f"isready\n"); p.stdin.flush()
    while q.get(timeout=10).strip()!="readyok": pass
    p.stdin.write(f"position fen {fen}\nisready\ngo infinite\n"); p.stdin.flush()
    t0=time.monotonic(); bm=None; at=None
    while time.monotonic()-t0 < WAIT:          # NO stop is sent in this window
        try: l=q.get(timeout=0.2)
        except queue.Empty: continue
        if l.startswith("bestmove"):
            bm=l.split()[1] if len(l.split())>1 else "?"; at=time.monotonic()-t0; break
    volunteered = bm is not None
    try:
        p.stdin.write("stop\nquit\n"); p.stdin.flush(); p.wait(timeout=5)
    except Exception: p.kill()
    return bm, at, volunteered
print(f"build {BUILD}\nsettings {describe()}\nwait window {WAIT}s with NO stop sent\n")
for label,fen in CASES:
    bm,at,vol=run(fen)
    print(f"  {label:16} bestmove={str(bm):6} at={('%.2fs'%at) if at else 'NEVER':7} volunteered={vol}")
