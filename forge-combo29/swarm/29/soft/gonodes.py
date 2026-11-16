#!/usr/bin/env python3
"""PC-path job: `go nodes N` for N = 20000, 50000, 250000 -- what the owner's matches use.

Questions that matter on this path:
  Q1 determinism at Threads 1 (must be exact),
  Q2 does it stop AT a completed iteration and at the node target (no soft-stop slack, unlike softnodes),
  Q3 legality and clean exit.

Fresh process per run, PC20, Threads 1, Hash 16. A run with no info line aborts.
"""
import subprocess, sys
EXE = sys.argv[1]
FENS = [l.strip() for l in open(sys.argv[2]) if l.strip()]
NS = [20000, 50000, 250000]
REPS = int(sys.argv[3]) if len(sys.argv) > 3 else 2
S14 = [("LmrQuietBase",93),("LmrQuietDivisor",205),("LmrNoisyBase",13),("LmrNoisyDivisor",333),
       ("LmrHistoryDivisor",5643),("NullMoveBase",5),("LmpBase",8),("HistoryPruneMultiplier",2220),
       ("HistoryBonusQuadratic",24),("HistoryBonusLinear",54),("HistoryBonusMax",2212),
       ("SingularDepth",6),("IirDepth",2),("NonPawnCorrection","true")]
PC20 = S14 + [("CuckooRep","true"),("HistRework",2),("TtPruneV2","true"),("CorrHistV2","true"),
              ("MateAlphaGuard","true"),("OwnBook","false")]
def go(fen, cmd):
    p=subprocess.Popen([EXE],stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True,bufsize=1)
    def s(x): p.stdin.write(x+"\n"); p.stdin.flush()
    s("uci")
    for l in p.stdout:
        if l.startswith("uciok"): break
    s("setoption name Hash value 16"); s("setoption name Threads value 1")
    for k,v in PC20: s(f"setoption name {k} value {v}")
    s("isready")
    for l in p.stdout:
        if l.startswith("readyok"): break
    s(f"position fen {fen}"); s(cmd)
    last=None; bm=None
    for l in p.stdout:
        if l.startswith("info depth"): last=l.rstrip()
        if l.startswith("bestmove"): bm=l.split()[1]; break
    s("quit"); p.wait(timeout=180)
    if last is None: raise SystemExit(f"ABORT: no info line for {cmd}")
    f=last.split()
    return int(f[2]), int(f[f.index("nodes")+1]), tuple(f[f.index("score")+1:f.index("score")+3]), bm
import chess
print(f"PC r15 build, PC20, Threads 1, Hash 16; {len(FENS)} positions; N in {NS}; {REPS} reps")
print()
print("| N | pos | reps identical? | depth | nodes | nodes/N | legal |")
print("|---|---|---|---|---|---|---|")
bad=0; nondet=0
for n in NS:
    for i,fen in enumerate(FENS,1):
        rows=[go(fen, f"go nodes {n}") for _ in range(REPS)]
        det = len(set(rows))==1
        if not det: nondet+=1
        b=chess.Board(fen); mv=rows[0][3]
        ok = (mv=="0000" and not any(b.legal_moves)) or (chess.Move.from_uci(mv) in b.legal_moves)
        if not ok: bad+=1
        d,nodes,sc,mv = rows[0]
        print(f"| {n} | {i} | {'YES' if det else '**NO**'} | {d} | {nodes} | {nodes/n:.2f} | {'YES' if ok else '**NO**'} |")
        if not det:
            print(f"|   |   | runs: {rows} | | | | |")
print()
print(f"nondeterministic positions: {nondet}   illegal/missing moves: {bad}")
