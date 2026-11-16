#!/usr/bin/env python3
"""clock99_builds.py : clock 99 vs 98 across BOTH builds and THREE settings, Threads 1, Hash 16.

Purpose (coordinator task 2): decide whether the clock-99 break predates the PC's r15 changes.
  base build  : default options, S14, and S14+the six PC20 options that EXIST on base (if any)
  PC r15 build: default options, S14, and PC20
If base breaks at 99 under S14 too, it predates the PC. If only PC20 breaks, one of the six options or an
r15 change introduced it.
Every cell prints score and nodes, so a collapse (tiny nodes + cp 0) is visible rather than assumed.
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
PC20_EXTRA = [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
              ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]
BOARD = "r4rk1/pp1b1ppp/4p3/3pP3/8/P3P3/1P2N1PP/R2R2K1 w - - {c} 1"


def options_of(exe):
    p = subprocess.run(shlex.split(exe), input="uci\nquit\n", capture_output=True, text=True, timeout=30)
    return {m.group(1) for m in re.finditer(r"^option name (.+?) type", p.stdout, re.M)}


def run(exe, fen, extra, threads=1, depth=10):
    p = subprocess.Popen(shlex.split(exe), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)

    def until(w):
        for l in p.stdout:
            if l.strip() == w:
                return
    p.stdin.write("uci\n"); p.stdin.flush(); until("uciok")
    p.stdin.write(f"setoption name Threads value {threads}\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write("setoption name Hash value 16\nisready\n"); p.stdin.flush(); until("readyok")
    for n, v in extra:
        p.stdin.write(f"setoption name {n} value {v}\n")
    p.stdin.write("isready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write("ucinewgame\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write(f"position fen {fen}\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write(f"go depth {depth}\n"); p.stdin.flush()
    last, best, errs = None, None, []
    while True:
        line = p.stdout.readline()
        if not line:
            break
        s = line.rstrip("\n")
        if "unknown option" in s or "invalid value" in s:
            errs.append(s)
        if s.startswith("info depth"):
            last = s
        if s.startswith("bestmove"):
            best = s.split()[-1]
            break
    p.stdin.write("quit\n"); p.stdin.flush()
    try:
        p.wait(timeout=10)
    except subprocess.TimeoutExpired:
        p.kill()
    m = re.search(r"score (cp|mate) (-?\d+)", last or "")
    n = re.search(r"nodes (\d+)", last or "")
    return ((m.group(1), int(m.group(2))) if m else None), best, (int(n.group(1)) if n else 0), errs


BUILDS = [("base", "/home/ubuntu/build/release/forge"), ("PC r15", "/home/ubuntu/build/pc/forge")]

for name, exe in BUILDS:
    avail = options_of(exe)
    pc20_here = [(n, v) for n, v in PC20_EXTRA if n in avail]
    regimes = [
        ("default", []),
        ("S14", S14),
        ("S14+PCopts", S14 + pc20_here),
    ]
    if name == "base":
        print(f"### {name}  (PC20 options present on this build: {[n for n, _ in pc20_here] or 'NONE'})")
    else:
        print(f"### {name}")
    for label, extra in regimes:
        row = []
        for c in (98, 99):
            sc, bm, nd, errs = run(exe, BOARD.format(c=c), extra)
            row.append((c, sc, nd, bm, errs))
        c98, c99 = row
        broke = (c99[1] == ("cp", 0) and c98[1] not in (None, ("cp", 0)))
        print(f"  {label:<12} clock98 {str(c98[1]):>11} nodes {c98[2]:>7} | "
              f"clock99 {str(c99[1]):>11} nodes {c99[2]:>7} | "
              f"{'BREAKS AT 99' if broke else 'no break'}"
              + (f"  ERRORS {c99[4][:1]}" if c99[4] else ""))
