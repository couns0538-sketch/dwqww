#!/usr/bin/env python3
"""Is the clock search's depth variation TIME-driven (expected) or a real nondeterminism (a defect)?

At Threads 1 with a fixed clock, the search stops when its time allocation runs out, so on a slow run it reaches a
shallower depth. The distinguishing test: run the SAME position at a FIXED NODE budget (`go nodes`) instead of a
clock. Node-budgeted searches must be exactly deterministic at Threads 1. If they are, the clock variation is the
timer, not the search.
"""
import subprocess, sys, statistics
EXE = sys.argv[1]
FEN = sys.argv[2]
S14 = [("LmrQuietBase",93),("LmrQuietDivisor",205),("LmrNoisyBase",13),("LmrNoisyDivisor",333),
       ("LmrHistoryDivisor",5643),("NullMoveBase",5),("LmpBase",8),("HistoryPruneMultiplier",2220),
       ("HistoryBonusQuadratic",24),("HistoryBonusLinear",54),("HistoryBonusMax",2212),
       ("SingularDepth",6),("IirDepth",2),("NonPawnCorrection","true")]
PC20 = S14 + [("CuckooRep","true"),("HistRework",2),("TtPruneV2","true"),("CorrHistV2","true"),
              ("MateAlphaGuard","true"),("OwnBook","false")]
def go(cmd):
    p=subprocess.Popen([EXE],stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True,bufsize=1)
    def s(x): p.stdin.write(x+"\n"); p.stdin.flush()
    s("uci")
    for line in p.stdout:
        if line.startswith("uciok"): break
    s("setoption name Hash value 16"); s("setoption name Threads value 1")
    for k,v in PC20: s(f"setoption name {k} value {v}")
    s("isready")
    for line in p.stdout:
        if line.startswith("readyok"): break
    s(f"position fen {FEN}")
    s(cmd)
    last=None; bm=None
    for line in p.stdout:
        if line.startswith("info depth"): last=line.rstrip()
        if line.startswith("bestmove"): bm=line.split()[1]; break
    s("quit"); p.wait(timeout=120)
    f=last.split()
    return int(f[2]), int(f[f.index("nodes")+1]), tuple(f[f.index("score")+1:f.index("score")+3]), bm
print(f"position: {FEN[:60]}")
print("\nA) FIXED NODE BUDGET (go nodes 300000), 4 runs -- must be identical at Threads 1:")
rows=[go("go nodes 300000") for _ in range(4)]
for r in rows: print(f"   depth {r[0]:>2} nodes {r[1]:>7} score {r[2]} move {r[3]}")
print(f"   distinct results: {len(set(rows))} of 4  -> {'DETERMINISTIC' if len(set(rows))==1 else 'NONDETERMINISTIC'}")
print("\nB) CLOCK (go wtime 6000 btime 6000 winc 60 binc 60), 6 runs -- depth may vary with speed:")
rows=[]
for _ in range(6):
    rows.append(go("go wtime 6000 btime 6000 winc 60 binc 60"))
for r in rows: print(f"   depth {r[0]:>2} nodes {r[1]:>7} score {r[2]} move {r[3]}")
print(f"   distinct depths: {sorted({r[0] for r in rows})};  distinct moves: {sorted({r[3] for r in rows})}")
