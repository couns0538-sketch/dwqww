#!/usr/bin/env python3
"""check_f7_fault.py EXE : applying seat 11's reasoning to S-F7 — is the 64-line burst a FAULT?

S-F7: on a root whose search resolves early (terminal, or a mate found), `go nodes N` emits 64 info lines at
0 nodes for depths 1..64 instead of stopping.

Seat 11's standard, applied: a behaviour is a fault only if it produces a WRONG result or an unusable one for a
real consumer. So test:
  F1  is the final line's move and score CORRECT on such a root? (compare with `go depth d`)
  F2  is the burst bounded (64 = the depth cap) or unbounded?
  F3  does a consumer reading the LAST info line get a sane answer?
  F4  does `go movetime` (a real match command) also burst, or only `go nodes`?
If F1 says the answer is right and F2 says it is bounded by the depth cap, then it is a cosmetic reporting
artefact, not a fault - and it should be recorded as such rather than as a defect.
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
CASES = [
    ("checkmated root", "8/8/Q7/8/8/K7/8/k1Q5 b - - 0 1"),
    ("mate in 1 root", "6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 0 1"),
    ("mate in 2 root", "1k6/8/1K6/8/8/8/8/R7 w - - 0 1"),
    ("ordinary middlegame", "rnb1kbnr/ppp1pppp/8/4q3/8/2N5/PPPP1PPP/R1BQKBNR w KQkq - 2 4"),
]


def run(fen, go):
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
    p.stdin.write(f"{go}\n"); p.stdin.flush()
    lines, best = [], None
    while True:
        line = p.stdout.readline()
        if not line:
            break
        s = line.rstrip("\n")
        if s.startswith("info depth"):
            lines.append(s)
        if s.startswith("bestmove"):
            best = s.split()[-1]
            break
    p.stdin.write("quit\n"); p.stdin.flush()
    try:
        p.wait(timeout=20)
    except subprocess.TimeoutExpired:
        p.kill()
    depths = []
    for l in lines:
        d = re.search(r"depth (\d+)", l)
        if d:
            depths.append(int(d.group(1)))
    score = "?"
    if lines:
        m = re.search(r"score (cp|mate) (-?\d+)", lines[-1])
        score = m.group(0) if m else "?"
    return len(lines), (max(depths) if depths else 0), best, score


print("### is the S-F7 burst a FAULT? — applying seat 11's standard")
print(f"{EXE}")
print()
print(f"{'case':<22} {'go nodes 50000':>16} {'':>3} {'go movetime 50':>16}   (lines / maxdepth / move)")
for name, fen in CASES:
    n1, d1, b1, s1 = run(fen, "go nodes 50000")
    n2, d2, b2, s2 = run(fen, "go movetime 50")
    print(f"{name:<22} {str(n1)+' / '+str(d1)+' / '+str(b1):>16} {'':>3} {str(n2)+' / '+str(d2)+' / '+str(b2):>16}")

print()
print("F1/F3 (is the answer right?): compare each root's final score/move at `go nodes 50000` with `go depth 10`:")
for name, fen in CASES:
    _, _, b1, s1 = run(fen, "go nodes 50000")
    _, _, b2, s2 = run(fen, "go depth 10")
    same = (b1 == b2 and s1 == s2)
    print(f"  {name:<22} nodes:{s1:>12} {str(b1):>6}   depth10:{s2:>12} {str(b2):>6}   same: {same}")
