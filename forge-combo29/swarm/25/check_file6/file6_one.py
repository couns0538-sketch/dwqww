#!/usr/bin/env python3
"""file6_one.py EXE FEN_TEMPLATE : one board through file 6's inequality, carefully.

Prints exactly the two numbers file 6 asks for, at several counters, so a "no" can be checked rather than
trusted. The first positive-control candidate already showed the interesting shape:
    board 8/8/8/8/3k4/8/8/K1Q5 w, counter 0 -> mate 8  (needs 2*8-1 = 15 half-moves)
    same board at counter 91  -> cp 0        (budget = 100 - 91 = 9)
    15 > 9, so the mate cannot finish before the match program ends the game -> correctly cp 0, NOT a defect.
This script maps how the budget and the mate distance interact as the counter changes, which is the honest way
to show the rule works and is not vacuous.
"""
import re
import shlex
import subprocess
import sys

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]
PC20 = [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
        ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]
EXE = sys.argv[1]
TPL = sys.argv[2]
DEPTH = 20


def run(fen):
    p = subprocess.Popen(shlex.split(EXE), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1)

    def until(w):
        for l in p.stdout:
            if l.strip() == w:
                return
    p.stdin.write("uci\n"); p.stdin.flush(); until("uciok")
    p.stdin.write("setoption name Threads value 1\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write("setoption name Hash value 16\nisready\n"); p.stdin.flush(); until("readyok")
    for n, v in S14 + PC20:
        p.stdin.write(f"setoption name {n} value {v}\n")
    p.stdin.write("isready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write("ucinewgame\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write(f"position fen {fen}\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write(f"go depth {DEPTH}\n"); p.stdin.flush()
    last = None
    while True:
        line = p.stdout.readline()
        if not line:
            break
        s = line.rstrip("\n")
        if s.startswith("info depth"):
            last = s
        if s.startswith("bestmove"):
            break
    p.stdin.write("quit\n"); p.stdin.flush()
    try:
        p.wait(timeout=20)
    except subprocess.TimeoutExpired:
        p.kill()
    m = re.search(r"score (cp|mate) (-?\d+)", last or "")
    return (m.group(1) if m else None), (int(m.group(2)) if m else None)


k0, v0 = run(TPL.format(c=0))
print(f"board: {TPL}")
print(f"counter 0 at depth {DEPTH}: {k0} {v0}")
if k0 == "mate" and v0 is not None:
    n = abs(v0)
    need = 2 * n - 1
    print(f"  a forced mate in {n} -> needs {need} half-moves")
    print()
    print(f"{'counter':>7} {'budget':>7} {'need':>5} {'in time?':>9} {'real score':>12} {'defect?':>8}")
    for c in (85, 88, 90, 91, 95, 99, 100):
        budget = 100 - c
        kr, vr = run(TPL.format(c=c))
        in_time = need <= budget
        real_zero = (kr == "cp" and vr == 0)
        defect = in_time and real_zero
        print(f"{c:>7} {budget:>7} {need:>5} {str(in_time):>9} {str(kr) + ' ' + str(vr):>12} {str(defect):>8}")
    print()
    print("Reading: the defect column should be False everywhere HERE, because at every counter where the budget")
    print("is big enough the engine also reports the mate (not cp 0), and where it reports cp 0 the budget is")
    print("too small. That is the rule behaving as designed - and it shows the rule is not vacuous: it names a")
    print("precise counter band in which the engine would be wrong if it reported 0.")
