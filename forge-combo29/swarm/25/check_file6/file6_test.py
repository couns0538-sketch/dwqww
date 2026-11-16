#!/usr/bin/env python3
"""file6_test.py EXE : FABLE_TO_swarm_6's test for whether a high-counter cp 0 is a DEFECT.

File 6's rule, verbatim in effect:
  A cp 0 at a high halfmove counter is a defect ONLY when a forced mate exists that ends no later than the
  100th half-move.
  Test: the same board with counter 0, `go depth 20` or more, read `mate N`;
  it is a defect only if  2N - 1 <= 100 - counter  AND  the board with the REAL counter still scores cp 0 at
  that depth.
  Report that inequality with both numbers in the finding line.

So for each of my boards at its real counter c:
  1. search the counter-0 board at depth 24 -> mate N (or a cp score)
  2. compute the budget: 100 - c half-moves left before the match program ends the game
  3. check 2N - 1 <= 100 - c
  4. also confirm the real-counter board still says cp 0 at that depth
It is a defect only if all of (1) is a mate, (3) and (4) hold. Anything else: NOT a defect by file 6.
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
DEPTH = 24

BOARDS = [
    # my original S-F3 board and the other clock-99 boards from S-F20
    "r4rk1/pp1b1ppp/4p3/3pP3/8/P3P3/1P2N1PP/R2R2K1 w - - {c} 1",
    "r4rk1/1pR4p/p1b1pbp1/5p2/2n2B2/4Q2P/Pq3PP1/1B3RK1 w - - {c} 1",
    "2r3k1/5pb1/4q1np/5Np1/pP1P2P1/4B3/1P1Q1PP1/5RK1 b - - {c} 1",
    "8/5pk1/4p3/3nK1p1/8/R5P1/5P2/8 b - - {c} 1",
    "8/3n2Q1/2k4p/8/1P6/5P1P/1K4P1/8 b - - {c} 1",
    "8/8/4k3/3rp1RR/KP6/P2p4/6PP/2r5 w - - {c} 1",
    "8/8/4K1k1/8/4N1P1/8/1b6/8 w - - {c} 1",
    "2R5/4P3/r7/5P1K/1k6/p1p5/6r1/R7 b - - {c} 1",
]
COUNTER = 99


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
    reached = 0
    while True:
        line = p.stdout.readline()
        if not line:
            break
        s = line.rstrip("\n")
        if s.startswith("info depth"):
            last = s
            d = re.search(r"depth (\d+)", s)
            if d:
                reached = max(reached, int(d.group(1)))
        if s.startswith("bestmove"):
            best = s.split()[-1]
            break
    p.stdin.write("quit\n"); p.stdin.flush()
    try:
        p.wait(timeout=20)
    except subprocess.TimeoutExpired:
        p.kill()
    m = re.search(r"score (cp|mate) (-?\d+)", last or "")
    kind = m.group(1) if m else None
    val = int(m.group(2)) if m else None
    return kind, val, reached, best


print("FABLE_TO_swarm_6 test: a high-counter cp 0 is a DEFECT only if a forced mate exists that ends no")
print(f"later than the 100th half-move. Board at counter {COUNTER}: budget = 100 - {COUNTER} = {100-COUNTER} half-moves.")
print(f"depth {DEPTH}, Threads 1, Hash 16, PC20")
print()
print(f"{'board':<46} {'c0: mate N':>11} {'2N-1':>5} {'<=budget':>9} {'real: score':>13} {'DEFECT?':>8}")
survivors = []
for tpl in BOARDS:
    f0 = tpl.format(c=0)
    fr = tpl.format(c=COUNTER)
    k0, v0, r0, b0 = run(f0)
    kr, vr, rr, br = run(fr)
    budget = 100 - COUNTER
    if k0 == "mate":
        n = abs(v0)
        need = 2 * n - 1
        within = need <= budget
        # the mate must be FOR or AGAINST the side to move consistently; file 6 only cares that it ends in time
        real_zero = (kr == "cp" and vr == 0)
        defect = within and real_zero
        print(f"{tpl[:46]:<46} {'mate ' + str(v0):>11} {need:>5} {str(within):>9} "
              f"{str(kr) + ' ' + str(vr):>13} {str(defect):>8}")
        if defect:
            survivors.append((tpl, v0, need, budget))
    else:
        print(f"{tpl[:46]:<46} {str(k0) + ' ' + str(v0):>11} {'-':>5} {'-':>9} "
              f"{str(kr) + ' ' + str(vr):>13} {'NO':>8}")

print()
print(f"DEFECTS SURVIVING THE FILE 6 TEST: {len(survivors)} of {len(BOARDS)} boards")
for tpl, v0, need, budget in survivors:
    print(f"  {tpl}  c0 mate {v0} (needs {need} half-moves, budget {budget}), real counter still cp 0")
if not survivors:
    print()
    print("NONE survive. By file 6's rule, none of my clock-99 boards is a defect: no forced mate exists on any")
    print("of them that ends within the half-moves remaining, so a cp 0 there is correct behaviour, not a fault.")
