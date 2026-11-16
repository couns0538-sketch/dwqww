#!/usr/bin/env python3
"""check_20F53.py EXE : does every "report without searching" path emit one info line per depth, capped at 64?

Seat 20's S-F53 generalises my S-F7: "any path that reports without searching emits one info-depth line per depth,
capped at 64 when no depth is given", evidenced by the empty-`searchmoves` path.

My S-C27 found the same shape on resolved roots but scoped it to "a root that resolves before the limit". If
seat 20's broader statement holds, the correct description of the family is theirs, not mine.

Tests: for each non-searching path, count info lines and max depth under (a) `go depth 5` and (b) `go nodes 50000`:
  P1  terminal root (checkmated)
  P2  empty searchmoves  (`go depth 5 searchmoves` with a legal-move set reduced to nothing)
  P3  resolved mate root
If every one caps at the requested depth under `go depth 5` and at 64 under `go nodes`, the generalisation holds.
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
    lines, strings, best = [], [], None
    while True:
        line = p.stdout.readline()
        if not line:
            break
        s = line.rstrip("\n")
        if s.startswith("info depth"):
            lines.append(s)
        elif s.startswith("info string"):
            strings.append(s)
        if s.startswith("bestmove"):
            best = s.split()[-1]
            break
    p.stdin.write("quit\n"); p.stdin.flush()
    try:
        p.wait(timeout=20)
    except subprocess.TimeoutExpired:
        p.kill()
    depth = 0
    for l in lines:
        d = re.search(r"depth (\d+)", l)
        if d:
            depth = max(depth, int(d.group(1)))
    return len(lines), depth, best, strings


CASES = [
    ("P1 terminal (checkmated)", "8/8/Q7/8/8/K7/8/k1Q5 b - - 0 1"),
    ("P3 resolved mate root", "6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 0 1"),
]
print("### seat 20's S-F53 generalisation vs my S-C27 scope")
print(f"{EXE}")
print()
print(f"{'path':<26} {'go depth 5':>16} {'go nodes 50000':>18}   (lines / maxdepth)")
for name, fen in CASES:
    n1, d1, b1, _ = run(fen, "go depth 5")
    n2, d2, b2, _ = run(fen, "go nodes 50000")
    print(f"{name:<26} {str(n1)+' / '+str(d1):>16} {str(n2)+' / '+str(d2):>18}")

print()
print("P2 empty searchmoves: a legal position with a searchmoves set that matches NO legal move")
n, d, b, strings = run("rnb1kbnr/ppp1pppp/8/4q3/8/2N5/PPPP1PPP/R1BQKBNR w KQkq - 2 4",
                       "go depth 5 searchmoves a7a8")
print(f"  go depth 5 searchmoves a7a8 -> {n} info lines, maxdepth {d}, bestmove {b}")
if strings:
    print(f"  info string lines: {strings[:2]}")
