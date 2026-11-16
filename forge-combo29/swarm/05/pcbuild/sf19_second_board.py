#!/usr/bin/env python3
"""sf19_second_board.py EXE -- is S-F19's finding (TtPruneV2 and MateAlphaGuard each fix the mate-PV truncation)
specific to G/192, or does it hold on other boards that truncate?

Candidate boards are taken from my own committed data: positions whose base-tree run had a mate score with a PV
shorter than 2|N|. From job1's criterion table that is G/192 only on the O+G run, but job1b's R set had R/120.
This script also scans a few boards of my R set on the BASE build first to find further truncating boards, then
tests those on the PC build under the three settings. Threads 1 throughout.
"""
import re
import subprocess
import sys
import time

BASE = "/tmp/build-rel/forge"
PC = "/tmp/build-pc/forge"
S14 = ["setoption name LmrQuietBase value 93", "setoption name LmrQuietDivisor value 205",
       "setoption name LmrNoisyBase value 13", "setoption name LmrNoisyDivisor value 333",
       "setoption name LmrHistoryDivisor value 5643", "setoption name NullMoveBase value 5",
       "setoption name LmpBase value 8", "setoption name HistoryPruneMultiplier value 2220",
       "setoption name HistoryBonusQuadratic value 24", "setoption name HistoryBonusLinear value 54",
       "setoption name HistoryBonusMax value 2212", "setoption name SingularDepth value 6",
       "setoption name IirDepth value 2", "setoption name NonPawnCorrection value true",
       "setoption name Threads value 1", "setoption name Hash value 16"]
TT = S14 + ["setoption name TtPruneV2 value true"]
MAG = S14 + ["setoption name MateAlphaGuard value true"]
DEPTH = 12

# boards from my committed data that showed a mate score on the base tree (job1 G set indices and job1b R set)
CANDIDATES = [
    ("G/59", "4Q3/8/r2K4/8/2B5/5R2/1k6/8 w - - 0 1"),
    ("G/184", "5K2/1p1k2Nb/4p3/4P3/8/P3q3/8/8 w - - 0 1"),
    ("G/192", "8/8/1p6/8/p3p3/8/2Kpk3/8 w - - 0 1"),
    ("G/196", "5Q2/1k6/3pK1PP/3P4/8/4N3/8/8 w - - 0 1"),
    ("G/217", "8/7p/8/7p/3k2b1/6K1/2p5/8 b - - 0 1"),
    ("G/306", "8/7k/7P/8/5pK1/4q3/8/8 b - - 0 1"),
    ("R/40", "R7/1P2k3/4B2p/8/2K2Pp1/8/1b6/8 b - - 2 109"),
]


def run(exe, opts, fen):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
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
        s(o); s("isready"); u("readyok")
    s("ucinewgame"); s("isready"); u("readyok")
    s(f"position fen {fen}"); s("isready")
    n0 = len(L)
    u("readyok")
    if any("invalid FEN" in x for x in L[n0:]):
        p.kill()
        return "REFUSED"
    s(f"go depth {DEPTH}"); u("bestmove"); s("quit")
    try:
        p.wait(timeout=25)
    except Exception:
        p.kill()
    pv = [x for x in L if re.search(r"\binfo\b.*\bpv\b", x)]
    if not pv:
        return "NO PV"
    last = pv[-1]
    m = re.search(r"score (mate|cp) (-?\d+)", last)
    if not m:
        return "NO SCORE"
    plies = len(last.split(" pv ", 1)[1].split()) if " pv " in last else 0
    kind, val = m.group(1), int(m.group(2))
    if kind != "mate" or val == 0:
        return f"{kind} {val:+d}"
    need = 2 * val - 1 if val > 0 else 2 * (-val)
    tag = "ok" if plies == need else f"SHORT {need - plies}"
    return f"mate {val:+d} pv{plies}/{need} {tag}"


print(f"depth {DEPTH}, Threads 1. BASE = base build + S14; PC columns = PC r15 build.")
print()
print("| board | BASE S14 | PC S14 | PC +TtPruneV2 only | PC +MateAlphaGuard only |")
print("|---|---|---|---|---|")
for label, fen in CANDIDATES:
    b = run(BASE, S14, fen)
    s = run(PC, S14, fen)
    t = run(PC, TT, fen)
    m = run(PC, MAG, fen)
    print(f"| {label} | {b} | {s} | {t} | {m} |")
print()
print("S-F19 is supported generally if the PC +TtPruneV2 and +MateAlphaGuard columns are never 'SHORT' while the")
print("PC S14 column is SHORT on the same board.")
