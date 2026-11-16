#!/usr/bin/env python3
"""Does S14-vs-PC20 bestmove AGREEMENT improve with depth, i.e. are the disagreements shallow-search noise?

If the two regimes converge as depth grows, the differences at low depth are horizon artefacts and PC20's pruning is
safe-but-noisy. If agreement stays flat, the regimes genuinely choose differently.

Threads 1, Hash 16, fresh process per search, drained to bestmove. Aborts on any missing bestmove.
"""
import subprocess, sys
EXE, FENS, N = sys.argv[1], sys.argv[2], int(sys.argv[3])
S14=[("LmrQuietBase",93),("LmrQuietDivisor",205),("LmrNoisyBase",13),("LmrNoisyDivisor",333),
     ("LmrHistoryDivisor",5643),("NullMoveBase",5),("LmpBase",8),("HistoryPruneMultiplier",2220),
     ("HistoryBonusQuadratic",24),("HistoryBonusLinear",54),("HistoryBonusMax",2212),
     ("SingularDepth",6),("IirDepth",2),("NonPawnCorrection","true")]
PC20=S14+[("CuckooRep","true"),("HistRework",2),("TtPruneV2","true"),("CorrHistV2","true"),
          ("MateAlphaGuard","true"),("OwnBook","false")]
fens=[l.strip() for l in open(FENS) if l.strip()][:N]
def mv(fen, st, depth):
    p=subprocess.Popen([EXE],stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True,bufsize=1)
    def s(c): p.stdin.write(c+"\n"); p.stdin.flush()
    s("uci")
    for l in p.stdout:
        if l.startswith("uciok"): break
    s("setoption name Hash value 16"); s("setoption name Threads value 1")
    for k,v in st: s(f"setoption name {k} value {v}")
    s("isready")
    for l in p.stdout:
        if l.startswith("readyok"): break
    s(f"position fen {fen}"); s(f"go depth {depth}")
    bm=None
    for l in p.stdout:
        if l.startswith("bestmove"): bm=l.split()[1]; break
    s("quit"); p.wait(timeout=600)
    if bm is None: raise SystemExit(f"ABORT: no bestmove for {fen[:30]} at depth {depth}")
    return bm
print("| depth | positions | same move | share |")
print("|---|---|---|---|")
for depth in (8, 10, 12, 14):
    same=0
    for fen in fens:
        if mv(fen,S14,depth)==mv(fen,PC20,depth): same+=1
    print(f"| {depth} | {len(fens)} | {same} | {100.0*same/len(fens):.1f} % |")
