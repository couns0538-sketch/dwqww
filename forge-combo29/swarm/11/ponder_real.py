#!/usr/bin/env python3
"""ponder_real.py EXE BUILD — ponder/ponderhit on the PC's path. A match program uses pondering;
check the engine answers correctly and does not hang. PC20, Threads 1."""
import os,re,sys,time,queue,subprocess,threading
sys.path.insert(0,'/agent/repos/dwqww/forge-combo29/swarm/11')
import chess
from pc20 import PC20_LINES
EXE=sys.argv[1]; BUILD=sys.argv[2] if len(sys.argv)>2 else "?"
def talk(cmds,wait=8.0):
    p=subprocess.Popen([EXE],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True,bufsize=1)
    q=queue.Queue()
    threading.Thread(target=lambda:[q.put(l.rstrip("\n")) for l in iter(p.stdout.readline,"")],daemon=True).start()
    p.stdin.write("uci\n"); p.stdin.flush()
    while q.get(timeout=10).strip()!="uciok": pass
    for line in PC20_LINES: p.stdin.write(line+"\n")
    p.stdin.write("isready\n"); p.stdin.flush()
    while q.get(timeout=10).strip()!="readyok": pass
    for c in cmds: p.stdin.write(c+"\n")
    p.stdin.flush()
    out=[]; t0=time.monotonic(); bm=None
    while time.monotonic()-t0<wait:
        try: l=q.get(timeout=0.2)
        except queue.Empty: continue
        out.append(l)
        if l.startswith("bestmove"): bm=l.split()[1]; break
    try: p.stdin.write("quit\n"); p.stdin.flush(); p.wait(timeout=5)
    except Exception: p.kill()
    return bm, out
FEN="rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2"
print(f"build {BUILD}  PC20, Threads 1\n")
bm,out=talk([f"position fen {FEN}","isready","go ponder wtime 6000 btime 6000 winc 60 binc 60"],wait=3)
print(f"  go ponder (no ponderhit, 3 s): bestmove={bm}  (None = correctly waits for ponderhit/stop)")
bm2,out2=talk([f"position fen {FEN}","isready","go ponder wtime 6000 btime 6000 winc 60 binc 60","ponderhit"],wait=8)
print(f"  go ponder + ponderhit         : bestmove={bm2}")
if bm2 and bm2!="0000":
    b=chess.Board(FEN)
    print(f"  that move legal: {chess.Move.from_uci(bm2) in b.legal_moves}")
bm3,out3=talk([f"position fen {FEN}","isready","go ponder wtime 6000 btime 6000 winc 60 binc 60","stop"],wait=5)
print(f"  go ponder + stop              : bestmove={bm3}")
