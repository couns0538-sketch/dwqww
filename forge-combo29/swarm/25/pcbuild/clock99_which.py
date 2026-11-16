#!/usr/bin/env python3
"""clock99_which.py EXE : which property makes clock 99 collapse? Compare V1 (breaks) with V3 (does not).

V1 breaks: r4rk1/pp1b1ppp/4p3/3pP3/8/P3P3/1P2N1PP/R2R2K1 w - - 99 1  -> cp 0, 341 nodes
V3 normal: r4rk1/pp1b1ppp/4p3/4P3/8/P1P5/1P2N1PP/R2R2K1 w - - 99 1   -> cp 597, 11360 nodes

Difference to test: a legal move that captures or pushes a pawn exists in BOTH (9 vs 9). So the difference must
be in what the lines LOOK like. The hypothesis to test: V1's every quiet line eventually runs to the fifty-move
horizon before anything decisive (its reset moves are bad/irrelevant), while V3 has a forcing line (d1d7)
whose first move is a capture/reset that the search actually chooses.

Test: for each board, ask the engine at depth 10 for its score at clock 99 and at clock 0. If the clock-0 score
is clearly non-zero and the clock-99 score is 0, the zero is a horizon artefact of the fifty-move rule inside
the search (a line that reaches the horizon loses its value), NOT a root shortcut.
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
PC20_EXTRA = [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
              ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]
EXE = sys.argv[1]


def run(fen, depth=10):
    p = subprocess.Popen(shlex.split(EXE), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)

    def until(w):
        for l in p.stdout:
            if l.strip() == w:
                return
    p.stdin.write("uci\n"); p.stdin.flush(); until("uciok")
    p.stdin.write("setoption name Threads value 1\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write("setoption name Hash value 16\nisready\n"); p.stdin.flush(); until("readyok")
    for n, v in S14 + PC20_EXTRA:
        p.stdin.write(f"setoption name {n} value {v}\n")
    p.stdin.write("isready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write("ucinewgame\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write(f"position fen {fen}\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write(f"go depth {depth}\n"); p.stdin.flush()
    infos, best = [], None
    while True:
        line = p.stdout.readline()
        if not line:
            break
        s = line.rstrip("\n")
        if s.startswith("info depth"):
            infos.append(s)
        if s.startswith("bestmove"):
            best = s.split()[-1]
            break
    p.stdin.write("quit\n"); p.stdin.flush()
    try:
        p.wait(timeout=10)
    except subprocess.TimeoutExpired:
        p.kill()
    return infos, best


BREAKS = "r4rk1/pp1b1ppp/4p3/3pP3/8/P3P3/1P2N1PP/R2R2K1 w - - {c} 1"
OK = "r4rk1/pp1b1ppp/4p3/4P3/8/P1P5/1P2N1PP/R2R2K1 w - - {c} 1"

for name, tpl in (("V1 (breaks)", BREAKS), ("V3 (normal)", OK)):
    print("=" * 72)
    print(name)
    for clock in (0, 99):
        infos, best = run(tpl.format(c=clock), depth=10)
        m = re.search(r"score (cp|mate) (-?\d+)", infos[-1]) if infos else None
        n = re.search(r"nodes (\d+)", infos[-1]) if infos else None
        depths = len(infos)
        print(f"  clock {clock:>2}: {m.group(0) if m else '?':>14} "
              f"nodes {n.group(1) if n else '?':>7} best {best} info_lines {depths}")
    # the full depth ladder at clock 99 shows whether the value collapses as depth grows
    infos, best = run(tpl.format(c=99), depth=10)
    print("  depth ladder at clock 99:")
    for l in infos:
        mm = re.search(r"depth (\d+).*score (cp|mate) (-?\d+).*nodes (\d+)", l)
        if mm:
            print(f"     depth {mm.group(1):>2} score {mm.group(2)} {mm.group(3):>6} nodes {mm.group(4):>6}")
