#!/usr/bin/env python3
"""`go nodes N` on the PC build (PC20, Threads 1, Hash 16) -- the hard-budget path the owner's matches use.

Beyond determinism, the questions that matter:
  Q1 is the search DETERMINISTIC (same depth/nodes/score/move every run)?
  Q2 does it STOP AT a completed iteration, i.e. does `go depth D` at its reported depth reproduce it exactly?
  Q3 how close does it get to the requested N -- and can it OVERSHOOT N, which for a hard budget it should not do
     by much (it may finish the iteration it is in)?
"""
import subprocess, sys
import chess

EXE = sys.argv[1]
FENS = [l.strip() for l in open(sys.argv[2]) if l.strip()]
NS = [20000, 50000, 250000]
REPS = 2
S14 = [("LmrQuietBase",93),("LmrQuietDivisor",205),("LmrNoisyBase",13),("LmrNoisyDivisor",333),
       ("LmrHistoryDivisor",5643),("NullMoveBase",5),("LmpBase",8),("HistoryPruneMultiplier",2220),
       ("HistoryBonusQuadratic",24),("HistoryBonusLinear",54),("HistoryBonusMax",2212),
       ("SingularDepth",6),("IirDepth",2),("NonPawnCorrection","true")]
PC20 = S14 + [("CuckooRep","true"),("HistRework",2),("TtPruneV2","true"),("CorrHistV2","true"),
              ("MateAlphaGuard","true"),("OwnBook","false")]

def go(fen, cmd):
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)
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
    last=None; bm=None; allines=[]
    for l in p.stdout:
        if l.startswith("info depth"):
            last=l.rstrip(); allines.append(l.rstrip())
        if l.startswith("bestmove"): bm=l.split()[1]; break
    s("quit"); p.wait(timeout=180)
    if last is None: raise SystemExit(f"ABORT: no info for {cmd}")
    f=last.split()
    return {"d":int(f[2]),"n":int(f[f.index("nodes")+1]),
            "sc":tuple(f[f.index("score")+1:f.index("score")+3]),"mv":bm,
            "pv":tuple(f[f.index("pv")+1:]) if "pv" in f else ()}

print("PC r15, PC20, Threads 1, Hash 16")
print("| N | pos | det(2) | depth | nodes | nodes/N | reproduces go depth D | legal |")
print("|---|---|---|---|---|---|---|---|")
nondet=0; miditer=0; illegal=0; over=[]
for n in NS:
    for i,fen in enumerate(FENS,1):
        a=go(fen,f"go nodes {n}"); b=go(fen,f"go nodes {n}")
        det = (a==b)
        if not det: nondet+=1
        d=go(fen,f"go depth {a['d']}")
        same = (a["sc"]==d["sc"] and a["mv"]==d["mv"] and a["pv"]==d["pv"])
        if not same: miditer+=1
        bd=chess.Board(fen)
        ok=(a["mv"]=="0000" and not any(bd.legal_moves)) or (chess.Move.from_uci(a["mv"]) in bd.legal_moves)
        if not ok: illegal+=1
        ratio=a["n"]/n
        if ratio>1.0: over.append((n,i,ratio))
        print(f"| {n} | {i} | {'YES' if det else '**NO**'} | {a['d']} | {a['n']} | {ratio:.2f} | "
              f"{'YES' if same else '**NO**'} | {'YES' if ok else '**NO**'} |")
        if not det:
            print(f"|   |   | runs differ: {a} vs {b} | | | | | |")
print()
print(f"nondeterministic: {nondet}   not reproducible by go depth D: {miditer}   illegal: {illegal}")
print(f"runs whose node count EXCEEDED N: {len(over)} of {len(NS)*len(FENS)}"
      + (f"  worst {max(o[2] for o in over):.2f}x at N={max(over,key=lambda x:x[2])[0]}" if over else ""))
