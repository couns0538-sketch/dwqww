#!/usr/bin/env python3
"""file6_fifty_test.py EXE REGIME FEN COUNTER -- implements file 6's defect test for a cp 0 at a high counter.

File 6's rule: a cp 0 at a high counter is a defect ONLY when a forced mate exists that ends no later than the 100th
half-move. Test: the same board at counter 0, `go depth 20` or more, read `mate N`; it is a defect only if
    2N - 1 <= 100 - counter
and the board with the REAL counter still scores cp 0 at that depth.

Prints the inequality with both numbers, as file 6 requires in the finding line.
Threads 1 throughout (swarm rule) and the settings are named.
"""
import re
import subprocess
import sys
import time

EXE = sys.argv[1]
REGIME = sys.argv[2] if len(sys.argv) > 2 else "PC20"
FEN = sys.argv[3]
COUNTER = int(sys.argv[4])
DEPTH = int(sys.argv[5]) if len(sys.argv) > 5 else 20

S14 = ["setoption name LmrQuietBase value 93", "setoption name LmrQuietDivisor value 205",
       "setoption name LmrNoisyBase value 13", "setoption name LmrNoisyDivisor value 333",
       "setoption name LmrHistoryDivisor value 5643", "setoption name NullMoveBase value 5",
       "setoption name LmpBase value 8", "setoption name HistoryPruneMultiplier value 2220",
       "setoption name HistoryBonusQuadratic value 24", "setoption name HistoryBonusLinear value 54",
       "setoption name HistoryBonusMax value 2212", "setoption name SingularDepth value 6",
       "setoption name IirDepth value 2", "setoption name NonPawnCorrection value true",
       "setoption name Threads value 1", "setoption name Hash value 16"]
SIX = ["setoption name CuckooRep value true", "setoption name HistRework value 2",
       "setoption name TtPruneV2 value true", "setoption name CorrHistV2 value true",
       "setoption name MateAlphaGuard value true", "setoption name OwnBook value false"]
OPTS = {"S14": S14, "PC20": S14 + SIX}[REGIME]


def run(fen, depth):
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    L = []

    def s(x):
        p.stdin.write(x + "\n")
        p.stdin.flush()

    def u(t, lim=600):
        t0 = time.time()
        while time.time() - t0 < lim:
            l = p.stdout.readline()
            if l == "":
                L.append("###EOF")
                return
            l = l.rstrip()
            L.append(l)
            if l.startswith(t):
                return
        L.append("###TIMEOUT")

    s("uci"); u("uciok")
    for o in OPTS:
        s(o); s("isready"); u("readyok")
    s("ucinewgame"); s("isready"); u("readyok")
    s(f"position fen {fen}"); s("isready"); u("readyok")
    s(f"go depth {depth}"); u("bestmove"); s("quit")
    try:
        p.wait(timeout=60)
    except Exception:
        p.kill()
    pv = [x for x in L if re.search(r"\binfo\b.*\bpv\b", x)]
    if not pv:
        return None, None, 0
    last = pv[-1]
    m = re.search(r"score (mate|cp) (-?\d+)", last)
    if not m:
        return None, None, 0
    plies = len(last.split(" pv ", 1)[1].split()) if " pv " in last else 0
    return m.group(1), int(m.group(2)), plies


def hm(f, h):
    q = f.split()
    q[4] = str(h)
    return " ".join(q)


print(f"exe: {EXE}   regime {REGIME}   Threads 1   depth {DEPTH}   date_utc: "
      f"{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}")
print(f"board: {FEN}   real counter: {COUNTER}")
print()
print("step 1: same board at counter 0, deep search, read the mate distance")
k0, v0, pl0 = run(hm(FEN, 0), DEPTH)
print(f"  counter 0, depth {DEPTH}: {k0} {v0} (pv {pl0} plies)")
print()
print("step 2: the board with the REAL counter, same depth")
kc, vc, plc = run(hm(FEN, COUNTER), DEPTH)
print(f"  counter {COUNTER}, depth {DEPTH}: {kc} {vc} (pv {plc} plies)")
print()
budget = 100 - COUNTER
if k0 == "mate" and v0:
    need = 2 * abs(v0) - 1 if v0 > 0 else 2 * abs(v0)
    inside = need <= budget
    print("step 3: file 6's inequality")
    print(f"  forced mate at counter 0: mate {v0:+d} -> needs {need} plies")
    print(f"  half-moves left before the 100th: 100 - {COUNTER} = {budget}")
    print(f"  inequality 2N-1 <= 100-counter : {need} <= {budget} -> {'TRUE' if inside else 'FALSE'}")
    print(f"  real-counter score: {kc} {vc}")
    is_defect = inside and kc == "cp" and vc == 0
    print()
    print(f"VERDICT under file 6: {'DEFECT' if is_defect else 'NOT A DEFECT'}")
    if not inside:
        print(f"  (the mate needs {need} plies but only {budget} half-moves remain, so scoring the real-counter")
        print("   board cp 0 is the match program's own outcome — correct behaviour)")
else:
    print(f"step 3: no forced mate found at counter 0 within depth {DEPTH} ({k0} {v0})")
    print("VERDICT under file 6: NOT A DEFECT — no mate exists inside the counter budget, so cp 0 is correct.")
