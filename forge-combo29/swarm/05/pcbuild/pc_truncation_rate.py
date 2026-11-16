#!/usr/bin/env python3
"""pc_truncation_rate.py EXE REGIME -- the mate-PV truncation rate on a given build/settings, over the SAME 28 mate
positions my base-build run had (extracted from committed rows.jsonl files, not re-selected after seeing results).

Rate on base build (S14, depth 12, Threads 1): 2 of 28 = 7.1%.
"""
import json
import re
import subprocess
import sys
import time

EXE = sys.argv[1]
REGIME = sys.argv[2] if len(sys.argv) > 2 else "PC20"
DEPTH = 12

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


def positions():
    out = []
    for path in ("../job1/out/rows.jsonl", "../job1b/outR/rows.jsonl"):
        for line in open(path):
            r = json.loads(line)
            lp = r.get("last_pv")
            if not lp:
                continue
            sc = lp.get("score", ("", 0))
            if sc[0] == "mate" and sc[1] != 0:
                out.append(r["fen"])
    return out


def run(fen):
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
        return ("REFUSED", None, None, None)
    s(f"go depth {DEPTH}"); u("bestmove"); s("quit")
    try:
        p.wait(timeout=25)
    except Exception:
        p.kill()
    pv = [x for x in L if re.search(r"\binfo\b.*\bpv\b", x)]
    if not pv:
        return ("NO PV", None, None, None)
    last = pv[-1]
    m = re.search(r"score (mate|cp) (-?\d+)", last)
    if not m:
        return ("NO SCORE", None, None, None)
    plies = len(last.split(" pv ", 1)[1].split()) if " pv " in last else 0
    return (m.group(1), int(m.group(2)), plies, last)


FENS = positions()
print(f"exe: {EXE}   regime: {REGIME}   depth {DEPTH}   Threads 1   date_utc: "
      f"{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}")
print(f"positions: {len(FENS)} (the same mate positions as the base-build run)")
print()
mate = 0
trunc = 0
lost = 0
detail = []
for fen in FENS:
    kind, val, plies, last = run(fen)
    if kind != "mate" or val in (None, 0):
        lost += 1
        detail.append((fen, f"{kind} {val}", "-", "-", "not a mate score"))
        continue
    mate += 1
    need = 2 * val - 1 if val > 0 else 2 * (-val)
    ok = (plies == need)
    if not ok:
        trunc += 1
    detail.append((fen, f"mate {val:+d}", need, plies, "ok" if ok else f"SHORT {need - plies}"))
print("| fen | score | need | pv plies | verdict |")
print("|---|---|---|---|---|")
for d in detail:
    print(f"| {d[0]} | {d[1]} | {d[2]} | {d[3]} | {d[4]} |")
print()
print(f"mate scores on this build: {mate} of {len(FENS)}  (base tree had 28)")
print(f"truncated: {trunc}  = {100.0*trunc/mate:.1f}% of mate scores   (base tree: 2/28 = 7.1%)")
print(f"no longer a mate score: {lost}")
