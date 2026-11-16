#!/usr/bin/env python3
"""sf1_minimal_fix.py EXE -- narrow WHICH PC20 options are needed for the S-F1 mate-PV truncation to disappear.

The one-at-a-time drop test (every single option removed, all else PC20) kept the PV consistent, so the fix is not
any single option. This tests cumulative subsets: each option added alone to S14, then pairs, then all six.
Board: G/192 = 8/8/1p6/8/p3p3/8/2Kpk3/8 w - - 0 1, depth 12, Threads 1. A row is CONSISTENT when the pv length
equals 2|N| for mate -N.
"""
import re
import subprocess
import sys
import time

EXE = sys.argv[1] if len(sys.argv) > 1 else "/tmp/build-pc/forge"
S14 = ["setoption name LmrQuietBase value 93", "setoption name LmrQuietDivisor value 205",
       "setoption name LmrNoisyBase value 13", "setoption name LmrNoisyDivisor value 333",
       "setoption name LmrHistoryDivisor value 5643", "setoption name NullMoveBase value 5",
       "setoption name LmpBase value 8", "setoption name HistoryPruneMultiplier value 2220",
       "setoption name HistoryBonusQuadratic value 24", "setoption name HistoryBonusLinear value 54",
       "setoption name HistoryBonusMax value 2212", "setoption name SingularDepth value 6",
       "setoption name IirDepth value 2", "setoption name NonPawnCorrection value true",
       "setoption name Threads value 1", "setoption name Hash value 16"]
SIX = [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
       ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]
FEN = "8/8/1p6/8/p3p3/8/2Kpk3/8 w - - 0 1"
DEPTH = 12


def run(extra):
    opts = S14 + [f"setoption name {n} value {v}" for n, v in extra]
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    L = []

    def s(x):
        p.stdin.write(x + "\n")
        p.stdin.flush()

    def u(t, lim=300):
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
    for o in opts:
        s(o); s("isready")
        n0 = len(L)
        u("readyok")
        if any("unknown option" in x or "invalid value" in x for x in L[n0:]):
            p.kill()
            return None
    s("ucinewgame"); s("isready"); u("readyok")
    s(f"position fen {FEN}"); s("isready"); u("readyok")
    s(f"go depth {DEPTH}"); u("bestmove"); s("quit")
    try:
        p.wait(timeout=20)
    except Exception:
        p.kill()
    pv = [x for x in L if re.search(r"\binfo\b.*\bpv\b", x)]
    if not pv:
        raise RuntimeError("NO PV — nothing measured")
    last = pv[-1]
    m = re.search(r"score (mate|cp) (-?\d+)", last)
    if not m:
        raise RuntimeError(f"NO SCORE: {last!r}")
    plies = len(last.split(" pv ", 1)[1].split()) if " pv " in last else 0
    return m.group(1), int(m.group(2)), plies


def verdict(kind, val, plies):
    if kind != "mate" or val == 0:
        return f"{kind} {val:+d} (no mate claim), pv {plies}"
    need = 2 * val - 1 if val > 0 else 2 * (-val)
    ok = "CONSISTENT" if plies == need else f"short by {need - plies}"
    return f"{kind} {val:+d}, pv {plies}/{need} -> {ok}"


print(f"exe: {EXE}   board: G/192   depth {DEPTH}   Threads 1")
print()
print("| options added to S14 | result |")
print("|---|---|")
for label, extra in [("(none — S14 alone)", [])] + \
                    [(f"only {n}", [(n, v)]) for n, v in SIX] + \
                    [("all six (PC20)", SIX)]:
    r = run(extra)
    if r is None:
        print(f"| {label} | REFUSED |")
        continue
    print(f"| {label} | {verdict(*r)} |")
print()
print("Then cumulative: options added one at a time in the listed order.")
print("| cumulative set | result |")
print("|---|---|")
acc = []
for n, v in SIX:
    acc = acc + [(n, v)]
    r = run(acc)
    label = " + ".join(x[0] for x in acc)
    if r is None:
        print(f"| {label} | REFUSED |")
        continue
    print(f"| {label} | {verdict(*r)} |")
