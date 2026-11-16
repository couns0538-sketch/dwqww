#!/usr/bin/env python3
"""options_test.py EXE -- the gap I flagged in check_25f4/RESULT.md: seat 25 reports that EvalRule50Damp,
depth range and UseNNUE false do not change their flat-99 result. I did not re-test that, so I test it here.

On seat 25's board at clock 99, depth 10, vary ONE thing at a time and report the score and node count.
A result of cp 0 with a small node count is the "draw shortcut". A real search would show real nodes.
"""
import re
import subprocess
import sys

EXE = sys.argv[1] if len(sys.argv) > 1 else "/tmp/build-rel/forge"
BOARD99 = "r4rk1/pp1b1ppp/4p3/3pP3/8/P3P3/1P2N1PP/R2R2K1 w - - 99 1"
BOARD0 = "r4rk1/pp1b1ppp/4p3/3pP3/8/P3P3/1P2N1PP/R2R2K1 w - - 0 1"

BASE = ["setoption name Threads value 1", "setoption name Hash value 16"]
S14 = ["setoption name LmrQuietBase value 93", "setoption name LmrQuietDivisor value 205",
       "setoption name LmrNoisyBase value 13", "setoption name LmrNoisyDivisor value 333",
       "setoption name LmrHistoryDivisor value 5643", "setoption name NullMoveBase value 5",
       "setoption name LmpBase value 8", "setoption name HistoryPruneMultiplier value 2220",
       "setoption name HistoryBonusQuadratic value 24", "setoption name HistoryBonusLinear value 54",
       "setoption name HistoryBonusMax value 2212", "setoption name SingularDepth value 6",
       "setoption name IirDepth value 2", "setoption name NonPawnCorrection value true"]


def run(fen, extra, depth=10):
    opts = BASE + S14 + extra
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         text=True, bufsize=1)
    out = []

    def send(s):
        p.stdin.write(s + "\n")
        p.stdin.flush()

    send("uci")
    for o in opts:
        send(o); send("isready")
    send("ucinewgame"); send("isready")
    send(f"position fen {fen}"); send("isready")
    send(f"go depth {depth}")
    bad = None
    while True:
        line = p.stdout.readline()
        if line == "":
            break
        line = line.rstrip("\n")
        out.append(line)
        for b in ("unknown option", "invalid value", "invalid FEN"):
            if b in line:
                bad = line
        if line.startswith("bestmove"):
            break
    send("quit")
    try:
        p.wait(timeout=20)
    except subprocess.TimeoutExpired:
        p.kill()
    if bad:
        return f"REJECTED ({bad})", None
    pv = [l for l in out if re.search(r"\binfo\b.*\bpv\b", l)]
    if not pv:
        return "NO_PV_LINE", None
    m = re.search(r"score (mate|cp) (-?\d+)", pv[-1])
    n = re.search(r"\bnodes (\d+)", pv[-1])
    return (f"{m.group(1)} {m.group(2)}" if m else "NO_SCORE"), (int(n.group(1)) if n else None)


print(f"exe: {EXE}")
print(f"board: {BOARD99}   go depth 10")
print()
CASES = [
    ("S14 baseline", []),
    ("EvalRule50Damp true", ["setoption name EvalRule50Damp value true"]),
    ("EvalRule50Damp false", ["setoption name EvalRule50Damp value false"]),
    ("UseNNUE false", ["setoption name UseNNUE value false"]),
    ("Hash 1", ["setoption name Hash value 1"]),
    ("Hash 1024", ["setoption name Hash value 1024"]),
    ("Threads 4", ["setoption name Threads value 4"]),
]
print("| case | score at clock 99 | nodes | note |")
print("|---|---|---|---|")
for label, extra in CASES:
    sc, nodes = run(BOARD99, extra)
    note = ""
    if sc.startswith("REJECTED"):
        note = "option name/value refused"
    print(f"| {label} | {sc} | {nodes} | {note} |")

print()
print("| depth | score at clock 99 | nodes |")
print("|---|---|---|")
for d in (1, 2, 5, 10, 16, 20):
    sc, nodes = run(BOARD99, [], d)
    print(f"| {d} | {sc} | {nodes} |")

print()
print("Control: the same board at clock 0 must search normally (so a 0 here is about the clock, not the board).")
sc, nodes = run(BOARD0, [])
print(f"| clock 0, depth 10 | {sc} | {nodes} |")
