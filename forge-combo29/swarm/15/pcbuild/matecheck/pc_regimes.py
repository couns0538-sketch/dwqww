#!/usr/bin/env python3
"""pc_regimes.py EXE FEN DEPTH : one search, one regime, prints score/nodes/bestmove + PV length.

Used to compare the same position across base/S14 and PC/PC20 so a finding line can say which build
and which settings it used. Threads 1 always. PARSE_FAIL rather than 0 on a missing token.
"""
import argparse, queue, re, subprocess, sys, threading, time
import chess

S14=[("LmrQuietBase","93"),("LmrQuietDivisor","205"),("LmrNoisyBase","13"),("LmrNoisyDivisor","333"),
("LmrHistoryDivisor","5643"),("NullMoveBase","5"),("LmpBase","8"),("HistoryPruneMultiplier","2220"),
("HistoryBonusQuadratic","24"),("HistoryBonusLinear","54"),("HistoryBonusMax","2212"),
("SingularDepth","6"),("IirDepth","2"),("NonPawnCorrection","true")]
PC20_EXTRA=[("CuckooRep","true"),("HistRework","2"),("TtPruneV2","true"),("CorrHistV2","true"),
("MateAlphaGuard","true"),("OwnBook","false")]

def opts(regime):
    return [] if regime=="none" else (S14 if regime=="S14" else S14+PC20_EXTRA)

def run(exe,o,fen,depth,limit=300):
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
    send("position fen "+fen); send("isready"); wait(lambda l:l=="readyok",30)
    send("go depth %d"%depth); bm=wait(lambda l:l.startswith("bestmove"),limit)
    try: send("quit"); p.wait(timeout=10)
    except Exception: p.kill()
    infos=[l for l in log if l.startswith("info depth")]
    last=infos[-1] if infos else None
    if not last: return dict(score="NO_INFO_LINE",nodes=None,pv=[],bestmove=bm,depth=None)
    m=re.search(r"score (cp|mate) (-?\d+)",last)
    score=("%s %s"%(m.group(1),m.group(2))) if m else "PARSE_FAIL"
    m2=re.search(r"\bnodes (\d+)",last); nodes=int(m2.group(1)) if m2 else "PARSE_FAIL"
    md=re.search(r"^info depth (\d+)",last); dep=int(md.group(1)) if md else None
    pv=last.split()[last.split().index("pv")+1:] if " pv " in last+" " else []
    bmtok=bm.split()[1] if bm and bm not in ("TIMEOUT","EOF") and len(bm.split())>1 else None
    return dict(score=score,nodes=nodes,pv=pv,bestmove=bmtok,depth=dep)

def pv_ok(fen,pv):
    b=chess.Board(fen)
    for u in pv:
        mv=chess.Move.from_uci(u)
        if mv not in b.legal_moves: return ("ILLEGAL_AT_"+u, None)
        b.push(mv)
    return ("legal", b.is_checkmate())

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("exe"); ap.add_argument("fen"); ap.add_argument("depth",type=int)
    ap.add_argument("--regime",default="S14")
    a=ap.parse_args()
    r=run(a.exe,opts(a.regime),a.fen,a.depth)
    st,mate=pv_ok(a.fen,r["pv"]) if r["pv"] else ("EMPTY_PV",None)
    want=None
    if r["score"].startswith("mate"):
        v=int(r["score"].split()[1]); want=(2*v-1 if v>0 else 2*abs(v))
    print("%-46s d%-3d %-10s nodes=%-8s pv=%-3d pv_state=%-12s ends_mate=%-5s want_plies=%-4s bm=%s"
          % (a.fen,a.depth,r["score"],r["nodes"],len(r["pv"]),st,mate,want,r["bestmove"]))
