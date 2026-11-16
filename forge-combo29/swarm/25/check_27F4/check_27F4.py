#!/usr/bin/env python3
"""check_27F4.py EXE LABEL : independent check of seat 27's S-F4.

Claim (seat 27): `setoption name Clear Hash` clears the transposition table but NOT the move-ordering
histories, so after a Clear Hash the same position at the same depth answers differently from a fresh process
(9 of 20 positions change bestmove, 19 of 20 change score, depth 10, S14).

My check, written from the claim: for N positions at depth 10 under S14, Threads 1, Hash 16, compare
  A  fresh process per position               (cold)
  B  one process: search, Clear Hash, search  (the claim says B differs from A)
  C  one process: search, ucinewgame, search  (my earlier audit says this equals A, a control that the
                                               comparison itself can detect difference)
Planted control (Rule 1): if no position differs in B, the harness cannot see a difference and the check is void.
Seat 10's rule is respected: ucinewgame is the cold baseline, Clear Hash is NOT.
"""
import re
import shlex
import subprocess
import sys

import chess

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]
PC20 = [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
        ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]
EXE = sys.argv[1]
LABEL = sys.argv[2]
FENS = sys.argv[3]
LIMIT = int(sys.argv[4]) if len(sys.argv) > 4 else 20
MODE = sys.argv[5] if len(sys.argv) > 5 else "PC20"
EXTRA = PC20 if MODE == "PC20" else []
DEPTH = 10


def _init(p):
    def until(w):
        for l in p.stdout:
            if l.strip() == w:
                return
    p.stdin.write("uci\n"); p.stdin.flush(); until("uciok")
    p.stdin.write("setoption name Threads value 1\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write("setoption name Hash value 16\nisready\n"); p.stdin.flush(); until("readyok")
    for n, v in S14 + EXTRA:
        p.stdin.write(f"setoption name {n} value {v}\n")
    p.stdin.write("isready\n"); p.stdin.flush(); until("readyok")


def _search(p, fen):
    def until(w):
        for l in p.stdout:
            if l.strip() == w:
                return
    p.stdin.write(f"position fen {fen}\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write(f"go depth {DEPTH}\n"); p.stdin.flush()
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
    m = re.search(r"score (cp|mate) (-?\d+)", last or "")
    return (m.group(0) if m else "?"), best


def fresh(fen):
    p = subprocess.Popen(shlex.split(EXE), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1)
    _init(p)
    sc, bm = _search(p, fen)
    p.stdin.write("quit\n"); p.stdin.flush()
    try:
        p.wait(timeout=10)
    except subprocess.TimeoutExpired:
        p.kill()
    return sc, bm


fens = [l.split(";")[0].strip() for l in open(FENS) if l.strip()][:LIMIT]
print(f"### check of seat 27 S-F4 — {LABEL}, {MODE}, Threads 1, Hash 16, depth {DEPTH}")
print(f"positions: {len(fens)}")

base = {(i): fresh(f) for i, f in enumerate(fens)}

# B: same process, search then Clear Hash then search again
p = subprocess.Popen(shlex.split(EXE), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                     stderr=subprocess.DEVNULL, text=True, bufsize=1)
_init(p)
bm_diff = sc_diff = 0
rows = []
for i, fen in enumerate(fens):
    first = _search(p, fen)
    def until(w):
        for l in p.stdout:
            if l.strip() == w:
                return
    p.stdin.write("setoption name Clear Hash\nisready\n"); p.stdin.flush(); until("readyok")
    second = _search(p, fen)
    d_bm = first[1] != second[1]
    d_sc = first[0] != second[0]
    bm_diff += d_bm
    sc_diff += d_sc
    rows.append((i, fen, first, second, d_bm, d_sc))
p.stdin.write("quit\n"); p.stdin.flush()
try:
    p.wait(timeout=10)
except subprocess.TimeoutExpired:
    p.kill()

print(f"after Clear Hash, bestmove changed in {bm_diff}/{len(fens)}, score changed in {sc_diff}/{len(fens)}")
for i, fen, a, b, dbm, dsc in rows:
    if dbm or dsc:
        print(f"  #{i} {fen[:52]}")
        print(f"      before: {a[0]} {a[1]}    after Clear Hash: {b[0]} {b[1]}")
print()
if bm_diff == 0 and sc_diff == 0:
    print("NO DIFFERENCE — either the claim does not reproduce on this build, or this harness cannot see it.")
    print("Because a zero needs a plant (Rule 1), this result is NOT shown unless the C control below differs.")
else:
    print(f"REPRODUCES seat 27 S-F4 on {LABEL}: Clear Hash does not restore the cold answer.")
