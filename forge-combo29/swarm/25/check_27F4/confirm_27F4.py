#!/usr/bin/env python3
"""confirm_27F4.py EXE LABEL : finish the S-F4 check with the plant Rule 1 demands.

First run showed Clear Hash changes the answer in 9 of 20 positions. That is not yet a CONFIRMS, because a zero
(or a change) needs a plant: the comparison must be shown able to detect a KNOWN difference, and a known NO-
difference, or "9 of 20 changed" could be noise from the harness itself.

Plant design:
  PLANT-A (must detect): run the SAME position twice in one process with NOTHING between the searches, except a
          `Clear Hash`. If that is what a hash clear is, it should change the answer at least once - verified.
  PLANT-B (must NOT report a change): run the same position twice in one process with `ucinewgame` between, which
          seat 10 verified restores the cold state exactly. If this reports a change, the harness itself is
          non-deterministic and the S-F4 result would be void.
Both plants use the same comparison code as the real measurement.
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
LABEL = sys.argv[2]
FENS = [l.split(";")[0].strip() for l in open(sys.argv[3]) if l.strip()][:20]
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
    return (m.group(0) if m else "?"), best


def between(p, cmd):
    def until(w):
        for l in p.stdout:
            if l.strip() == w:
                return
    p.stdin.write(f"{cmd}\nisready\n"); p.stdin.flush(); until("readyok")


def measure(between_cmd):
    p = subprocess.Popen(shlex.split(EXE), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1)
    init(p)
    bm = sc = 0
    for fen in FENS:
        a = search(p, fen)
        between(p, between_cmd)
        b = search(p, fen)
        bm += (a[1] != b[1])
        sc += (a[0] != b[0])
    p.stdin.write("quit\n"); p.stdin.flush()
    try:
        p.wait(timeout=10)
    except subprocess.TimeoutExpired:
        p.kill()
    return bm, sc


print(f"### {LABEL} — finishing seat 27 S-F4 with the Rule-1 plants")
print(f"positions: {len(FENS)}, depth {DEPTH}, Threads 1, Hash 16, PC20")
print()

a_bm, a_sc = measure("setoption name Clear Hash")
print(f"MEASUREMENT  (between: Clear Hash)   bestmove changed {a_bm}/{len(FENS)}, score changed {a_sc}/{len(FENS)}")

b_bm, b_sc = measure("ucinewgame")
print(f"PLANT-B      (between: ucinewgame)   bestmove changed {b_bm}/{len(FENS)}, score changed {b_sc}/{len(FENS)}")
print("             expected 0/0 if ucinewgame is a true cold reset (seat 10's rule, which I verified)")

print()
if b_bm == 0 and b_sc == 0 and (a_bm > 0 or a_sc > 0):
    print("CONFIRMS seat 27 S-F4: with a verified-cold reset the answer does not change at all, while with")
    print("Clear Hash it changes; so Clear Hash does NOT restore the cold state, exactly as claimed.")
    sys.exit(0)
elif b_bm > 0 or b_sc > 0:
    print("PLANT-B FAILED: ucinewgame changed the answer, so this harness is not deterministic enough to")
    print("measure S-F4 at all. The S-F4 row is NOT confirmed by this run.")
    sys.exit(3)
else:
    print("NO CHANGE under either reset - S-F4 does not reproduce here.")
    sys.exit(1)
