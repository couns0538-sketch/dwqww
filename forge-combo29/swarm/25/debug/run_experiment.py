#!/usr/bin/env python3
"""run_experiment.py EXE : the clock-99 experiment, three cases, stderr instrumentation captured.

Cases, all depth 6, Threads 1, Hash 16, PC20 (the settings the break was found under):
  A  breaking board, clock 99   r4rk1/pp1b1ppp/4p3/3pP3/8/P3P3/1P2N1PP/R2R2K1 w - - 99 1
  B  non-breaking middlegame, clock 99  r4rk1/pp1b1ppp/4p3/4P3/8/P1P5/1P2N1PP/R2R2K1 w - - 99 1
  C  control: the breaking board at clock 98  (normal search expected)

stdout (the info lines) and stderr (the [DBG ...] instrumentation) are captured SEPARATELY so the answer can
be read as "which test fired" rather than inferred from the score.
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

CASES = [
    ("A breaking, clock 99", "r4rk1/pp1b1ppp/4p3/3pP3/8/P3P3/1P2N1PP/R2R2K1 w - - 99 1"),
    ("B non-breaking, clock 99", "r4rk1/pp1b1ppp/4p3/4P3/8/P1P5/1P2N1PP/R2R2K1 w - - 99 1"),
    ("C control, breaking board clock 98", "r4rk1/pp1b1ppp/4p3/3pP3/8/P3P3/1P2N1PP/R2R2K1 w - - 98 1"),
]


def run(exe, fen, depth=6):
    p = subprocess.Popen(shlex.split(exe), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, text=True, bufsize=1)

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
            best = s
            break
    p.stdin.write("quit\n"); p.stdin.flush()
    try:
        p.wait(timeout=10)
    except subprocess.TimeoutExpired:
        p.kill()
    err = p.stderr.read()
    return infos, best, err


exe = sys.argv[1]
for name, fen in CASES:
    infos, best, err = run(exe, fen)
    print("=" * 78)
    print(name)
    print(f"  FEN: {fen}")
    last = infos[-1] if infos else "(none)"
    m = re.search(r"score (cp|mate) (-?\d+)", last)
    n = re.search(r"nodes (\d+)", last)
    toks = last.split()
    pv = toks[toks.index("pv") + 1:] if "pv" in toks else []
    print(f"  RESULT: {m.group(0) if m else '?'}  nodes {n.group(1) if n else '?'}  "
          f"pv {len(pv)} plies  {best}")
    print("  --- stderr instrumentation ---")
    interesting = [l for l in err.split("\n")
                   if "[DBG ROOT-SHORTCUT PATH TAKEN]" in l or "[DBG EMERGENCY" in l
                   or "[DBG root]" in l or "[DBG ROOT ITER SEARCHED]" in l]
    for l in interesting:
        print("   ", l)
    hits = [l for l in err.split("\n") if "[DBG is_draw TRUE" in l]
    # summarise the is_draw hits: which sub-test fired, and on which FENs
    sub = {}
    for l in hits:
        for key in ("fifty=True", "rep=True", "insuf=True", "nomove=True"):
            if key in l:
                sub[key.split("=")[0]] = sub.get(key.split("=")[0], 0) + 1
    print(f"  --- is_draw TRUE lines: {len(hits)}  by sub-test: {sub}")
    for l in hits[:4]:
        print("   ", l)
    print()
