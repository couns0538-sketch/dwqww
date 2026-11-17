#!/usr/bin/env python3
"""Does PC20's smaller tree translate to WALL TIME on real games, or only to fewer nodes?

F42 established PC20 searches 10.7-11.9 % fewer nodes at match depths. Fewer nodes should mean less time, but nodes
are not time: the switches themselves cost work per node (CuckooRep, HistRework, TtPruneV2, CorrHistV2 all do extra
bookkeeping). So the honest question is whether wall time improves AT ALL.

Design: interleaved ABBA over positions, both regimes, measuring wall ms from sending `go` to reading `bestmove`.
Threads 1, Hash 16, fresh process per search. Reports the paired ratio and a bootstrap interval.
"""
import random, statistics, subprocess, sys, time
EXE, FENS, N = sys.argv[1], sys.argv[2], int(sys.argv[3])
DEPTH = int(sys.argv[4]) if len(sys.argv) > 4 else 12
S14=[("LmrQuietBase",93),("LmrQuietDivisor",205),("LmrNoisyBase",13),("LmrNoisyDivisor",333),
     ("LmrHistoryDivisor",5643),("NullMoveBase",5),("LmpBase",8),("HistoryPruneMultiplier",2220),
     ("HistoryBonusQuadratic",24),("HistoryBonusLinear",54),("HistoryBonusMax",2212),
     ("SingularDepth",6),("IirDepth",2),("NonPawnCorrection","true")]
PC20=S14+[("CuckooRep","true"),("HistRework",2),("TtPruneV2","true"),("CorrHistV2","true"),
          ("MateAlphaGuard","true"),("OwnBook","false")]
fens=[l.strip() for l in open(FENS) if l.strip()][:N]
def one(fen, st):
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
    s(f"position fen {fen}")
    t0=time.monotonic(); s(f"go depth {DEPTH}")
    bm=None
    for l in p.stdout:
        if l.startswith("bestmove"): bm=l.split()[1]; break
    ms=(time.monotonic()-t0)*1000.0
    s("quit"); p.wait(timeout=900)
    if bm is None: raise SystemExit(f"ABORT: no bestmove for {fen[:30]}")
    return ms
pairs=[]
for i,fen in enumerate(fens):
    if i%2==0:
        a=one(fen,S14); b=one(fen,PC20)
    else:
        b=one(fen,PC20); a=one(fen,S14)
    pairs.append((a,b))
sa=[p[0] for p in pairs]; sb=[p[1] for p in pairs]
r=[y/x for x,y in pairs]
random.seed(2901)
boots=sorted(statistics.mean([random.choice(r) for _ in r]) for _ in range(10000))
lo,hi=boots[250],boots[9750]; m=statistics.mean(r)
print(f"depth {DEPTH}, {len(pairs)} positions, Threads 1, Hash 16, interleaved ABBA")
print(f"| metric | S14 | PC20 |")
print(f"|---|---|---|")
print(f"| median wall ms | {statistics.median(sa):.0f} | {statistics.median(sb):.0f} |")
print(f"| mean wall ms | {statistics.mean(sa):.0f} | {statistics.mean(sb):.0f} |")
print()
print(f"PC20/S14 time ratio = {m:.4f} -> {100*(1/m-1):+.2f}% speed, 95% CI [{lo:.4f}, {hi:.4f}]")
print("verdict:", "PC20 faster (CI below 1)" if hi<1.0 else ("PC20 slower (CI above 1)" if lo>1.0 else "INDISTINGUISHABLE"))
