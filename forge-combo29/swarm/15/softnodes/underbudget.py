#!/usr/bin/env python3
"""underbudget.py EXE : why did G-end-2 stop at 442 nodes for N=500 and N=2000?

Reruns that exact board five more times at N=500 (softnodes) and also at N=2000 and with
`go nodes`, recording for EVERY run: the full depth sequence, the last info line, whether a mate
score appears, and the bestmove. If the stop is at the same node count every time, something about
the POSITION stops it, not the budget.
Threads 1, PC20.
"""
import queue, re, subprocess, threading, time
import chess

S14=[("LmrQuietBase","93"),("LmrQuietDivisor","205"),("LmrNoisyBase","13"),("LmrNoisyDivisor","333"),
("LmrHistoryDivisor","5643"),("NullMoveBase","5"),("LmpBase","8"),("HistoryPruneMultiplier","2220"),
("HistoryBonusQuadratic","24"),("HistoryBonusLinear","54"),("HistoryBonusMax","2212"),
("SingularDepth","6"),("IirDepth","2"),("NonPawnCorrection","true")]
PC20=S14+[("CuckooRep","true"),("HistRework","2"),("TtPruneV2","true"),("CorrHistV2","true"),
("MateAlphaGuard","true"),("OwnBook","false")]
FEN="k7/6R1/5N2/p4K1P/P7/8/8/8 b - - 0 1"

def run(exe, goname):
    p=subprocess.Popen([exe],stdin=subprocess.PIPE,stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,text=True,bufsize=1)
    q=queue.Queue()
    def rd():
        for l in p.stdout: q.put(l.rstrip("\n"))
        q.put(None)
    threading.Thread(target=rd,daemon=True).start()
    def send(c): p.stdin.write(c+"\n"); p.stdin.flush()
    def wait(pred,lim):
        t0=time.monotonic()
        while True:
            rem=lim-(time.monotonic()-t0)
            if rem<=0: return None
            try: l=q.get(timeout=rem)
            except queue.Empty: return None
            if l is None: return None
            if pred(l): return l
    send("uci"); wait(lambda l:l.startswith("uciok"),30)
    send("setoption name Threads value 1"); send("setoption name Hash value 16")
    for k,v in PC20: send("setoption name %s value %s"%(k,v))
    send("isready"); wait(lambda l:l=="readyok",30)
    send("ucinewgame"); send("isready"); wait(lambda l:l=="readyok",30)
    send("position fen "+FEN); send("isready"); wait(lambda l:l=="readyok",30)
    send("go "+goname)
    infos=[];bm=None
    t0=time.monotonic()
    while time.monotonic()-t0<200:
        try: l=q.get(timeout=1.0)
        except queue.Empty: continue
        if l is None: break
        if l.startswith("info depth"): infos.append(l)
        if l.startswith("bestmove"): bm=l; break
    send("quit")
    try: p.wait(timeout=10)
    except: p.kill()
    return infos, bm

print("board: %s  (black to move, black is lost)" % FEN)
b=chess.Board(FEN)
print("legal moves: %d   checkmate now: %s   stalemate now: %s"
      % (b.legal_moves.count(), b.is_checkmate(), b.is_stalemate()))
print()
print("=== go softnodes 500, five repeat runs ===")
for i in range(5):
    infos,bm=run("/home/ubuntu/builds/pc/forge","softnodes 500")
    if not infos:
        print("  run%d: NO INFO LINES  %s" % (i+1,bm)); continue
    last=infos[-1]
    m=re.search(r"score (cp|mate) (-?\d+)",last); m2=re.search(r"\bnodes (\d+)",last)
    md=re.search(r"^info depth (\d+)",last)
    print("  run%d: depth=%s nodes=%s score=%s  %s" % (i+1, md.group(1) if md else "?",
          m2.group(1) if m2 else "?", "%s %s"%(m.group(1),m.group(2)) if m else "?",
          bm.split()[1] if bm and len(bm.split())>1 else bm))
print()
print("=== full info lines of one run (to see why it stopped) ===")
infos,bm=run("/home/ubuntu/builds/pc/forge","softnodes 500")
for l in infos: print("  "+l)
print("  "+str(bm))
