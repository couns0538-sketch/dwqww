#!/usr/bin/env python3
"""position_midsearch.py EXE BUILD — sending a NEW position while a search runs. A GUI may do this
on a takeback/desync. Does the engine stop the old search, answer it, or hang? PC20, Threads 1."""
import os,re,sys,time,queue,subprocess,threading
sys.path.insert(0,'/agent/repos/dwqww/forge-combo29/swarm/11')
from pc20 import PC20_LINES
EXE=sys.argv[1]; BUILD=sys.argv[2] if len(sys.argv)>2 else "?"
FEN1="r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R b KQkq - 3 3"
FEN2="rnbqkbnr/ppp2ppp/8/3pp3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 0 3"
def scenario(delay_ms, newcmd):
    p=subprocess.Popen([EXE],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True,bufsize=1)
    q=queue.Queue()
    threading.Thread(target=lambda:[q.put(l.rstrip("\n")) for l in iter(p.stdout.readline,"")],daemon=True).start()
    p.stdin.write("uci\n"); p.stdin.flush()
    while q.get(timeout=10).strip()!="uciok": pass
    for line in PC20_LINES: p.stdin.write(line+"\n")
    p.stdin.write("isready\n"); p.stdin.flush()
    while q.get(timeout=10).strip()!="readyok": pass
    p.stdin.write(f"position fen {FEN1}\nisready\ngo depth 30\n"); p.stdin.flush()
    time.sleep(delay_ms/1000.0)
    p.stdin.write(newcmd+"\n"); p.stdin.flush()
    # then ask for a normal search and see whether it responds
    time.sleep(0.4)
    p.stdin.write(f"position fen {FEN2}\nisready\ngo nodes 20000\n"); p.stdin.flush()
    t0=time.monotonic(); bms=[]; readyoks=0
    while time.monotonic()-t0<8:
        try: l=q.get(timeout=0.2)
        except queue.Empty: continue
        if l.startswith("bestmove"): bms.append(l.split()[1])
        if l.strip()=="readyok": readyoks+=1
    hung = len(bms)==0
    try: p.stdin.write("quit\n"); p.stdin.flush(); p.wait(timeout=5)
    except Exception: p.kill()
    return bms, readyoks, hung
print(f"build {BUILD}  PC20, Threads 1 — new position sent 300 ms into a go depth 30\n")
for label,cmd in (("position fen (new game)", f"position fen {FEN2}"), ("ucinewgame", "ucinewgame"), ("stop", "stop")):
    bms,rok,hung=scenario(300,cmd)
    print(f"  interrupt with {label:26} -> bestmoves {bms} readyoks {rok} hung={hung}")
