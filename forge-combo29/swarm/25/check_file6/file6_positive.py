#!/usr/bin/env python3
"""file6_positive.py EXE : the file 6 test applied where it CAN fire.

At counter 99 the budget is 1 half-move, so nothing can qualify (proved on my 8 boards). File 6's rule can only
fire at a counter with enough budget for a real mate: e.g. counter 91 -> 9 half-moves -> a mate in 5 or fewer.
File 6 names exactly that case ("seat 05's K+R against K at counter 91: a draw unless that board has a mate in 5
or fewer").

This script builds and tests candidates at counters 91..80 where a forced mate plausibly exists, and applies the
inequality strictly. If it finds a real one, that is a genuine defect with the numbers file 6 asks for.
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
DEPTH = 20


def run(fen, depth=DEPTH):
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
    p.stdin.write(f"go depth {depth}\n"); p.stdin.flush()
    last, best = None, None
    while True:
        line = p.stdout.readline()
        if not line:
            break
        s = line.rstrip("\n")
        if s.startswith("info depth"):
            last = s
        if s.startswith("bestmove"):
            best = s.split()[-1]
            break
    p.stdin.write("quit\n"); p.stdin.flush()
    try:
        p.wait(timeout=20)
    except subprocess.TimeoutExpired:
        p.kill()
    m = re.search(r"score (cp|mate) (-?\d+)", last or "")
    return (m.group(1) if m else None), (int(m.group(2)) if m else None), best


# Mate-in-N endgames: K+Q vs K (mate in 1..3 possible), K+R vs K (needs more), Q+R vs K.
# Each expressed as a board where the WINNER is to move, so the engine should report a positive mate N.
CANDIDATES = [
    # K+Q vs K, white to move, several distances
    ("KQ vs K, mate soon", "8/8/8/8/8/2k5/8/K1Q5 w - - {c} 1"),
    ("KQ vs K b", "8/8/8/8/3k4/8/8/K1Q5 w - - {c} 1"),
    ("KQ vs K c", "8/8/8/4k3/8/8/8/K1Q5 w - - {c} 1"),
    # K+R vs K (the file-6 named case: draw unless mate in 5 or fewer)
    ("KR vs K a", "8/8/8/4k3/8/8/8/K1R5 w - - {c} 1"),
    ("KR vs K b", "8/8/8/8/4k3/8/8/K1R5 w - - {c} 1"),
    # Q+R vs K (forced mate, usually short)
    ("QR vs K", "8/8/8/4k3/8/8/8/K1QR4 w - - {c} 1"),
]
COUNTERS = (91, 85, 80)

print("File 6's inequality applied where it can fire (budget = 100 - counter).")
print(f"depth {DEPTH}, Threads 1, Hash 16, PC20")
print()
print(f"{'candidate':<22} {'ctr':>4} {'budget':>7} {'c0 score':>10} {'2N-1':>5} {'in time':>8} {'real ctr':>10} {'DEFECT':>7}")
found = []
for name, tpl in CANDIDATES:
    for c in COUNTERS:
        k0, v0, b0 = run(tpl.format(c=0))
        kr, vr, br = run(tpl.format(c=c))
        budget = 100 - c
        if k0 == "mate" and v0 is not None and v0 > 0:
            need = 2 * v0 - 1
            in_time = need <= budget
            real_zero = (kr == "cp" and vr == 0)
            defect = in_time and real_zero
            print(f"{name:<22} {c:>4} {budget:>7} {'mate ' + str(v0):>10} {need:>5} "
                  f"{str(in_time):>8} {str(kr) + ' ' + str(vr):>10} {str(defect):>7}")
            if defect:
                found.append((name, tpl, c, v0, need, budget, vr))
        else:
            print(f"{name:<22} {c:>4} {budget:>7} {str(k0)+' '+str(v0):>10} {'-':>5} {'-':>8} "
                  f"{str(kr)+' '+str(vr):>10} {'no':>7}")

print()
if found:
    print(f"REAL DEFECTS FOUND: {len(found)}")
    for name, tpl, c, v0, need, budget, vr in found:
        print(f"  {name}: {tpl.format(c=c)} -> board at counter 0 is mate {v0} ({need} half-moves), "
              f"budget {budget}, and the real-counter board still scores cp {vr}")
else:
    print("No candidate satisfies file 6's inequality: in every case either the counter-0 board has no forced")
    print("mate, or the mate needs more half-moves than the budget, or the real-counter board does not score 0.")
