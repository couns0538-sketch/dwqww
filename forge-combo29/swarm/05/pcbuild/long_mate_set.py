#!/usr/bin/env python3
"""long_mate_set.py EXE -- build a mate-position set that is DELIBERATELY weighted to long mates (|N| >= 8), because
S-F30 showed a random sample cannot test S-F27's rule (|N| >= 10 truncates, |N| < 10 does not).

Method: take candidate positions, search at depth 20 (deep enough that the reported mate distance is the engine's
best current estimate), keep those reporting |N| >= 8, then re-search at depth 12 under the same settings and apply the
2N-1 rule. This SELECTS for long mates before the depth-12 measurement, which is not the same as selecting after
seeing whether they truncate.

Usage: long_mate_set.py EXE S14|PC20 [POOL]
"""
import re
import subprocess
import sys
import time

EXE = sys.argv[1]
REGIME = sys.argv[2] if len(sys.argv) > 2 else "S14"
POOL = int(sys.argv[3]) if len(sys.argv) > 3 else 150

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

    def u(t, lim=400):
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
    s(f"position fen {fen}"); s("isready")
    n0 = len(L)
    u("readyok")
    if any("invalid FEN" in x for x in L[n0:]):
        p.kill()
        return None
    s(f"go depth {depth}"); u("bestmove"); s("quit")
    try:
        p.wait(timeout=40)
    except Exception:
        p.kill()
    pv = [x for x in L if re.search(r"\binfo\b.*\bpv\b", x)]
    if not pv:
        return None
    last = pv[-1]
    m = re.search(r"score (mate|cp) (-?\d+)", last)
    if not m:
        return None
    plies = len(last.split(" pv ", 1)[1].split()) if " pv " in last else 0
    return (m.group(1), int(m.group(2)), plies)


cands = []
for line in open("../job1/data/G.epd"):
    cands.append(line.split(";")[0].strip())
for line in open("../job1b/positions/R_seed511.fens"):
    cands.append(line.strip())
cands = [c for c in cands if c][:POOL]

print(f"exe: {EXE}   regime {REGIME}   Threads 1   pool {len(cands)}   date_utc: "
      f"{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}")
print("stage 1: depth 20, keep positions whose mate distance is |N| >= 8")
longs = []
for fen in cands:
    r = run(fen, 20)
    if r and r[0] == "mate" and r[1] != 0 and abs(r[1]) >= 8:
        longs.append((fen, r[1]))
print(f"  {len(longs)} positions with |N| >= 8 at depth 20")
print()
print("stage 2: re-search those at depth 12, apply the 2N-1 rule")
print("| fen | |N| at d20 | d12 score | need | pv plies | verdict |")
print("|---|---|---|---|---|---|")
trunc = 0
mate12 = 0
for fen, n20 in longs:
    r = run(fen, 12)
    if not r:
        print(f"| {fen} | {abs(n20)} | NO PV | - | - | - |")
        continue
    kind, val, plies = r
    if kind != "mate" or val == 0:
        print(f"| {fen} | {abs(n20)} | {kind} {val:+d} | - | {plies} | not a mate score |")
        continue
    mate12 += 1
    need = 2 * val - 1 if val > 0 else 2 * (-val)
    ok = plies == need
    if not ok:
        trunc += 1
    print(f"| {fen} | {abs(n20)} | mate {val:+d} | {need} | {plies} | {'ok' if ok else f'SHORT {need - plies}'} |")
print()
print(f"long-mate positions: {len(longs)}   mate scores at d12: {mate12}   truncated: {trunc}"
      f" = {100.0*trunc/mate12 if mate12 else 0:.1f}%")
