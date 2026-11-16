#!/usr/bin/env python3
"""repcount2.py EXE --regime R : repetition counts 1/2/3/4 with node counts, plus insufficient material.

Answers two open questions on the PC build:
  (a) at which occurrence count (if any) is a repeated root declared drawn,
  (b) are insufficient-material roots SEARCHED (nodes > 0) or short-circuited (0 nodes).
Threads 1 throughout. A value that cannot be parsed is PARSE_FAIL, never 0.
"""
import argparse, queue, re, subprocess, threading, time
import chess

S14=[("LmrQuietBase","93"),("LmrQuietDivisor","205"),("LmrNoisyBase","13"),("LmrNoisyDivisor","333"),
("LmrHistoryDivisor","5643"),("NullMoveBase","5"),("LmpBase","8"),("HistoryPruneMultiplier","2220"),
("HistoryBonusQuadratic","24"),("HistoryBonusLinear","54"),("HistoryBonusMax","2212"),
("SingularDepth","6"),("IirDepth","2"),("NonPawnCorrection","true")]
PC20_EXTRA=[("CuckooRep","true"),("HistRework","2"),("TtPruneV2","true"),("CorrHistV2","true"),
("MateAlphaGuard","true"),("OwnBook","false")]
CYCLE=["g1f3","g8f6","f3g1","f6g8"]

def key(b): return (b.board_fen(),b.turn,b.castling_xfen(),b.ep_square)

def build(cycles):
    b=chess.Board(); mv=[]; c={key(b):1}
    for _ in range(cycles):
        for u in CYCLE:
            b.push(chess.Move.from_uci(u)); mv.append(u); c[key(b)]=c.get(key(b),0)+1
    return mv, c[key(b)]

def opts(regime):
    return [] if regime=="none" else (S14 if regime=="S14" else S14+PC20_EXTRA)

def run(exe,o,poscmd,go="depth 10",limit=180):
    p=subprocess.Popen([exe],stdin=subprocess.PIPE,stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,text=True,bufsize=1)
    q=queue.Queue(); log=[]
    def rd():
        for line in p.stdout: q.put(line.rstrip("\n"))
        q.put(None)
    threading.Thread(target=rd,daemon=True).start()
    def send(c): p.stdin.write(c+"\n"); p.stdin.flush()
    def wait(pred,lim):
        t0=time.monotonic()
        while True:
            rem=lim-(time.monotonic()-t0)
            if rem<=0: return "TIMEOUT"
            try: line=q.get(timeout=rem)
            except queue.Empty: return "TIMEOUT"
            if line is None: return "EOF"
            log.append(line)
            if pred(line): return line
    send("uci"); wait(lambda l:l.startswith("uciok"),30)
    send("setoption name Threads value 1"); send("setoption name Hash value 16")
    for k,v in o: send("setoption name %s value %s"%(k,v))
    send("isready"); wait(lambda l:l=="readyok",30)
    send("ucinewgame"); send("isready"); wait(lambda l:l=="readyok",30)
    send(poscmd); send("isready"); wait(lambda l:l=="readyok",30)
    send("go "+go); bm=wait(lambda l:l.startswith("bestmove"),limit)
    try: send("quit"); p.wait(timeout=10)
    except Exception: p.kill()
    infos=[l for l in log if l.startswith("info depth")]
    last=infos[-1] if infos else None
    sc=nd=None
    if last:
        m=re.search(r"score (cp|mate) (-?\d+)",last); sc=("%s %s"%(m.group(1),m.group(2))) if m else "PARSE_FAIL"
        m2=re.search(r"\bnodes (\d+)",last); nd=int(m2.group(1)) if m2 else "PARSE_FAIL"
    return sc,nd,bm,len(infos)

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("exe"); ap.add_argument("--regime",default="PC20")
    a=ap.parse_args(); o=opts(a.regime)
    print("exe: %s regime: %s Threads 1"%(a.exe,a.regime),flush=True)
    print("%-12s %-6s %-10s %-9s %-11s %-6s %s"%("occurrences","plies","score","nodes","bestmove","infos","verdict"),flush=True)
    for cyc in (0,1,2,3):
        mv,occ=build(cyc); assert occ==cyc+1,(occ,cyc+1)
        cmd="position startpos"+(" moves "+" ".join(mv) if mv else "")
        sc,nd,bm,n=run(a.exe,o,cmd)
        v="DECLARED DRAWN (0 nodes)" if (sc=="cp 0" and nd==0) else "searched"
        print("%-12d %-6d %-10s %-9s %-11s %-6d %s"%(occ,len(mv),sc,nd,bm,n,v),flush=True)
    print(flush=True)
    print("=== insufficient material: searched or short-circuited? ===",flush=True)
    print("%-40s %-10s %-9s %-11s %s"%("fen","score","nodes","bestmove","verdict"),flush=True)
    for fen,label in [("8/8/4k3/8/8/4K3/8/8 w - - 0 1","K v K"),
                      ("8/8/4k3/8/8/4K3/5N2/8 w - - 0 1","KN v K"),
                      ("8/8/4k3/8/8/4K3/5B2/8 w - - 0 1","KB v K")]:
        sc,nd,bm,n=run(a.exe,o,"position fen "+fen)
        v="SHORT-CIRCUITED (0 nodes)" if nd==0 else "SEARCHED"
        print("%-40s %-10s %-9s %-11s %s (%s)"%(fen,sc,nd,bm,v,label),flush=True)

main()
