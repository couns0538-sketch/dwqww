#!/usr/bin/env python3
"""mate_sample_pc.py EXE REGIME NPOOL -- builds a LARGER mate-position sample and measures the truncation rate on
the given build/settings, so the 0-of-27 in S-F23 is not read as a precise rate from a tiny sample.

Method: search a pool of positions at depth 8 first (cheap), keep the ones that report a mate score, then re-search
those at depth 12 and apply the 2N-1 rule. Positions come from the R set already in my folder plus the G set, so
nothing is selected after seeing the depth-12 result.
"""
import json
import re
import subprocess
import sys
import time

EXE = sys.argv[1]
REGIME = sys.argv[2] if len(sys.argv) > 2 else "PC20"
POOL = int(sys.argv[3]) if len(sys.argv) > 3 else 120

S14 = ["setoption name LmrQuietBase value 93", "setoption name LmrQuietDivisor value 205",
       "setoption name LmrNoisyBase value 13", "setoption name LmrNoisyDivisor value 333",
       "setoption name LmrHistoryDivisor value 5643", "setoption name NullMoveBase value 5",
       "setoption name LmpBase value 8", "setoption name HistoryPruneMultiplier value 2220",
       "setoption name HistoryBonusQuadratic value 24", "setoption name HistoryBonusLinear value 54",
       "setoption name HistoryBonusMax value 2212", "setoption name SingularDepth value 6",
       "setoption name IirDepth value 2", "setoption name NonPawnCorrection value true",
       "setoption name Threads value 1", "setoption name Hash value 16"]
PC20 = S14 + ["setoption name CuckooRep value true", "setoption name HistRework value 2",
              "setoption name TtPruneV2 value true", "setoption name CorrHistV2 value true",
              "setoption name MateAlphaGuard value true", "setoption name OwnBook value false"]
OPTS = {"PC20": PC20, "S14": S14}[REGIME]


def run(fen, depth):
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
        p.wait(timeout=25)
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


def pool():
    out = []
    try:
        for line in open("../job1b/positions/R_seed511.fens"):
            out.append(line.strip())
    except FileNotFoundError:
        pass
    for line in open("../job1/data/G.epd"):
        out.append(line.split(";")[0].strip())
    return [f for f in out if f][:POOL]


FENS = pool()
print(f"exe: {EXE}   regime {REGIME}   Threads 1   pool {len(FENS)}   date_utc: "
      f"{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}")
print("stage 1: depth 8 screen for positions reporting a mate score")
mates = []
for i, fen in enumerate(FENS):
    r = run(fen, 8)
    if r and r[0] == "mate" and r[1] != 0:
        mates.append((fen, r[1]))
print(f"  {len(mates)} positions reported a mate at depth 8")
print("stage 2: re-search those at depth 12 and apply the 2N-1 rule")
trunc = 0
mate12 = 0
lost = 0
rows = []
for fen, _m8 in mates:
    r = run(fen, 12)
    if not r:
        lost += 1
        continue
    kind, val, plies = r
    if kind != "mate" or val == 0:
        lost += 1
        rows.append((fen, f"{kind} {val:+d}", "-", "-", "not a mate score at d12"))
        continue
    mate12 += 1
    need = 2 * val - 1 if val > 0 else 2 * (-val)
    ok = plies == need
    if not ok:
        trunc += 1
    rows.append((fen, f"mate {val:+d}", need, plies, "ok" if ok else f"SHORT {need - plies}"))
print()
print("| fen | d12 score | need | pv plies | verdict |")
print("|---|---|---|---|---|")
for r in rows:
    print(f"| {r[0]} | {r[1]} | {r[2]} | {r[3]} | {r[4]} |")
print()
print(f"mate scores at depth 12: {mate12}")
print(f"truncated: {trunc} = {100.0*trunc/mate12 if mate12 else 0:.1f}%")
print(f"lost (not a mate score at depth 12): {lost}")
