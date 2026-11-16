#!/usr/bin/env python3
"""isolate_state.py EXE : is the in-process difference caused by the RESET, or just by searching twice?

confirm_27F4 showed that BOTH `Clear Hash` (4/20 bestmove, 18/20 score changed) and `ucinewgame` (6/20, 18/20)
change the answer between two searches in one process. If `ucinewgame` is a true cold reset - which I verified
earlier on ONE position, 18407 nodes three times - then either

  (a) that single-position verification was too narrow and repeated searches in one process differ anyway, or
  (b) something else in the harness (output parsing, option persistence) is at play.

This script isolates it with four arithmetics on the SAME 20 positions:
  R1  two searches back to back, NOTHING between
  R2  two searches with ucinewgame between
  R3  two searches with Clear Hash between
  R4  two searches each in its own FRESH process (the reference: must differ 0/20)
and additionally compares NODE counts, which are the sharpest signal (a cold search of the same position at the
same depth must give an identical node count).
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
FENS = [l.split(";")[0].strip() for l in open(sys.argv[2]) if l.strip()][:20]
DEPTH = 10


def init(p):
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


def search(p, fen):
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
    n = re.search(r"nodes (\d+)", last or "")
    return (m.group(0) if m else "?"), best, (int(n.group(1)) if n else 0)


def between(p, cmd):
    if not cmd:
        return
    def until(w):
        for l in p.stdout:
            if l.strip() == w:
                return
    p.stdin.write(f"{cmd}\nisready\n"); p.stdin.flush(); until("readyok")


def two_searches(cmd):
    p = subprocess.Popen(shlex.split(EXE), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1)
    init(p)
    d_bm = d_sc = d_nodes = 0
    for fen in FENS:
        a = search(p, fen)
        between(p, cmd)
        b = search(p, fen)
        d_bm += a[1] != b[1]
        d_sc += a[0] != b[0]
        d_nodes += a[2] != b[2]
    p.stdin.write("quit\n"); p.stdin.flush()
    try:
        p.wait(timeout=10)
    except subprocess.TimeoutExpired:
        p.kill()
    return d_bm, d_sc, d_nodes


def fresh_pair():
    d_bm = d_sc = d_nodes = 0
    for fen in FENS:
        out = []
        for _ in range(2):
            p = subprocess.Popen(shlex.split(EXE), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                 stderr=subprocess.DEVNULL, text=True, bufsize=1)
            init(p)
            out.append(search(p, fen))
            p.stdin.write("quit\n"); p.stdin.flush()
            try:
                p.wait(timeout=10)
            except subprocess.TimeoutExpired:
                p.kill()
        a, b = out
        d_bm += a[1] != b[1]
        d_sc += a[0] != b[0]
        d_nodes += a[2] != b[2]
    return d_bm, d_sc, d_nodes


n = len(FENS)
print(f"### {EXE}")
print(f"positions: {n}, depth {DEPTH}, Threads 1, Hash 16, PC20")
print()
print(f"{'setup':<38} {'bestmove':>10} {'score':>10} {'nodes':>10}")
for label, cmd in (("R4 two FRESH processes (reference)", None),
                   ("R1 back to back, nothing between", ""),
                   ("R2 ucinewgame between", "ucinewgame"),
                   ("R3 Clear Hash between", "setoption name Clear Hash")):
    r = fresh_pair() if cmd is None else two_searches(cmd)
    print(f"{label:<38} {r[0]:>6}/{n:<3} {r[1]:>6}/{n:<3} {r[2]:>6}/{n:<3}")
print()
print("Reading: R4 must be 0/0/0. If R2 (ucinewgame) is also 0 and R1/R3 are not, then Clear Hash is the")
print("difference and seat 27 S-F4 is confirmed. If R2 is NOT 0, then repeated searches differ for another")
print("reason and the earlier 'reproduction' was measuring that, not S-F4.")
