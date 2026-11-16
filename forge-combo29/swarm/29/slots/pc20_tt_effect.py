#!/usr/bin/env python3
"""Does the PC20 option set change how much WORK the TT does per position, on real games?

Profiles the PC r15 build at depth 12 over real-game positions under S14 and under PC20, Threads 1, Hash 16, and
reports (a) total probes, (b) probes per position, (c) the share of run instructions inside probe_body's symbol
family, so the question "is the table more expensive on the PC's settings" gets a measured answer rather than an
assumption.

Fresh process per regime, drained to bestmove. Aborts if a regime reports no node count.
"""
import subprocess, sys
EXE, FENS, N = sys.argv[1], sys.argv[2], int(sys.argv[3])
DEPTH = int(sys.argv[4]) if len(sys.argv)>4 else 12
HASH = int(sys.argv[5]) if len(sys.argv)>5 else 16
S14=[("LmrQuietBase",93),("LmrQuietDivisor",205),("LmrNoisyBase",13),("LmrNoisyDivisor",333),
     ("LmrHistoryDivisor",5643),("NullMoveBase",5),("LmpBase",8),("HistoryPruneMultiplier",2220),
     ("HistoryBonusQuadratic",24),("HistoryBonusLinear",54),("HistoryBonusMax",2212),
     ("SingularDepth",6),("IirDepth",2),("NonPawnCorrection","true")]
PC20=S14+[("CuckooRep","true"),("HistRework","true" and 2),("TtPruneV2","true"),("CorrHistV2","true"),
          ("MateAlphaGuard","true"),("OwnBook","false")]
fens=[l.strip() for l in open(FENS) if l.strip()][:N]
def run(settings):
    p=subprocess.Popen([EXE],stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True,bufsize=1)
    def s(c): p.stdin.write(c+"\n"); p.stdin.flush()
    s("uci")
    for l in p.stdout:
        if l.startswith("uciok"): break
    s(f"setoption name Hash value {HASH}"); s("setoption name Threads value 1")
    for k,v in settings: s(f"setoption name {k} value {v}")
    s("isready")
    for l in p.stdout:
        if l.startswith("readyok"): break
    nodes=0; npos=0
    for f in fens:
        s(f"position fen {f}"); s(f"go depth {DEPTH}")
        last=None
        for l in p.stdout:
            if l.startswith("info depth"): last=l
            if l.startswith("bestmove"): break
        if last is None: raise SystemExit("ABORT: no info line -- nothing measured")
        f2=last.split(); nodes+=int(f2[f2.index("nodes")+1]); npos+=1
    s("quit"); p.wait(timeout=1800)
    return nodes, npos
print(f"depth {DEPTH}, Hash {HASH}, Threads 1, PC r15 build")
print()
print("| regime | positions | total nodes | nodes/position |")
print("|---|---|---|---|")
for lbl,st in (("S14",S14),("PC20",PC20)):
    n,pos=run(st)
    print(f"| {lbl} | {pos} | {n:,} | {n//pos:,} |")
