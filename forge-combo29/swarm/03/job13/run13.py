#!/usr/bin/env python3
"""run13.py EXE OUTFILE : the four positive-cost positions at `go nodes 20000`, one fresh process per search,
PC20, Threads 1, Hash 16. Reports the chosen move and, for each candidate, its score; plus whether the engine
reported a terminal/drawn root at all (a cp 0 with 0 info depth lines at the root would be that)."""
import os, re, subprocess, sys
import chess
EXE, OUT = sys.argv[1], sys.argv[2]
CASES=[(6,"8/8/8/8/8/4Kp2/8/5k2 w - - 0 14","e3f3","e3d3"),
       (22,"5K2/8/5P2/6k1/8/8/8/8 b - - 0 13","g5f6","g5g6"),
       (37,"8/5p2/5K2/8/5k2/8/8/8 w - - 0 7","f6f7","f6g7"),
       (44,"8/2K5/3r4/8/8/8/2k5/8 w - - 0 10","c7d6","c7b8")]
PC20=[("LmrQuietBase","93"),("LmrQuietDivisor","205"),("LmrNoisyBase","13"),("LmrNoisyDivisor","333"),
      ("LmrHistoryDivisor","5643"),("NullMoveBase","5"),("LmpBase","8"),("HistoryPruneMultiplier","2220"),
      ("HistoryBonusQuadratic","24"),("HistoryBonusLinear","54"),("HistoryBonusMax","2212"),("SingularDepth","6"),
      ("IirDepth","2"),("NonPawnCorrection","true"),("CuckooRep","true"),("HistRework","2"),("TtPruneV2","true"),
      ("CorrHistV2","true"),("MateAlphaGuard","true"),("OwnBook","false")]
raw=open(OUT+".raw","w")
def go(fen, move=None):
    p=subprocess.Popen([EXE],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,bufsize=1)
    def s(c): p.stdin.write(c+"\n"); p.stdin.flush()
    def u(t):
        lines=[]
        while True:
            l=p.stdout.readline()
            if l=="": raise RuntimeError("died waiting "+t)
            raw.write(l); lines.append(l.strip())
            if l.strip().startswith(t): return lines
    s("uci");u("uciok");s("isready");u("readyok")
    for o,v in [("Threads","1"),("Hash","16")]+PC20:
        s(f"setoption name {o} value {v}"); s("isready"); u("readyok")
    s("ucinewgame");s("isready");u("readyok")
    s(f"position fen {fen}");s("isready");u("readyok")
    s("go nodes 20000"+(f" searchmoves {move}" if move else ""))
    lines=[]
    while True:
        l=p.stdout.readline()
        if l=="": raise RuntimeError("died before bestmove")
        raw.write(l); lines.append(l.strip())
        if l.strip().startswith("bestmove"): break
    s("quit")
    try: p.wait(timeout=120)
    except Exception: p.kill()
    bm=[x for x in lines if x.startswith("bestmove")][0].split()[1]
    infos=[x for x in lines if x.startswith("info depth")]
    sc=None
    for x in reversed(lines):
        m=re.search(r"score (cp|mate) (-?\d+).*?nodes (\d+)",x)
        if m and x.startswith("info"):
            sc=(m.group(1),int(m.group(2)),int(m.group(3))); break
    return bm, sc, len(infos)
out=["exe: "+EXE,"budget: go nodes 20000, PC20, Threads 1, Hash 16, fresh process per search","",
     "| idx | free choice | chosen score (nodes) | alt score (nodes) | info lines |","|---|---|---|---|---|"]
for idx,fen,ch,alt in CASES:
    bm,sc,n=go(fen)
    _,scc,_=go(fen,ch)
    _,sca,_=go(fen,alt)
    out.append(f"| {idx} | {bm} | {scc[0]} {scc[1]} ({scc[2]}) | {sca[0]} {sca[1]} ({sca[2]}) | {n} |")
    print(out[-1],flush=True)
raw.close()
open(OUT,"w").write("\n".join(out)+"\n")
