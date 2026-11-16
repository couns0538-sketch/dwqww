#!/usr/bin/env python3
"""isolate_options.py EXE FEN DEPTH -- searches the same FEN at the same depth under four option sets and
prints the mate score each time, to find WHICH option changes the reported mate distance:
  A: engine defaults
  B: Threads 1 + Hash 16 only
  C: full S14 + Threads 1 + Hash 16
  D: full S14 but NonPawnCorrection false, and E: full S14 with IirDepth left at default
"""
import re
import subprocess
import sys
import time

EXE, FEN, DEPTH = sys.argv[1], sys.argv[2], int(sys.argv[3])
BAD = ("unknown option", "invalid value", "invalid FEN", "illegal move")

S14 = [
    "setoption name LmrQuietBase value 93", "setoption name LmrQuietDivisor value 205",
    "setoption name LmrNoisyBase value 13", "setoption name LmrNoisyDivisor value 333",
    "setoption name LmrHistoryDivisor value 5643", "setoption name NullMoveBase value 5",
    "setoption name LmpBase value 8", "setoption name HistoryPruneMultiplier value 2220",
    "setoption name HistoryBonusQuadratic value 24", "setoption name HistoryBonusLinear value 54",
    "setoption name HistoryBonusMax value 2212", "setoption name SingularDepth value 6",
    "setoption name IirDepth value 2", "setoption name NonPawnCorrection value true",
]
SETS = {
    "A_defaults": [],
    "B_threads_hash_only": ["setoption name Threads value 1", "setoption name Hash value 16"],
    "C_full_S14": ["setoption name Threads value 1", "setoption name Hash value 16"] + S14,
    "D_S14_no_NonPawnCorrection": ["setoption name Threads value 1", "setoption name Hash value 16"] +
                                  [o for o in S14 if "NonPawnCorrection" not in o],
    "E_S14_no_IirDepth": ["setoption name Threads value 1", "setoption name Hash value 16"] +
                         [o for o in S14 if "IirDepth" not in o],
}


def run(options):
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         text=True, bufsize=1)

    def send(s):
        p.stdin.write(s + "\n")
        p.stdin.flush()

    def until(tok, limit=300):
        got = []
        t0 = time.time()
        while time.time() - t0 < limit:
            line = p.stdout.readline()
            if line == "":
                got.append("### EOF")
                break
            line = line.rstrip("\n")
            got.append(line)
            if line.startswith(tok):
                break
            if any(b in line for b in BAD):
                got.append("### HARNESS_STOP")
                break
        return got

    send("uci")
    until("uciok")
    for o in options:
        send(o)
        send("isready")
        r = until("readyok")
        if any("###" in x for x in r):
            p.kill()
            return f"HARNESS_STOP on {o}"
    send("ucinewgame")
    send("isready")
    until("readyok")
    send(f"position fen {FEN}")
    send("isready")
    until("readyok")
    send(f"go depth {DEPTH}")
    block = until("bestmove")
    send("quit")
    try:
        p.wait(timeout=10)
    except subprocess.TimeoutExpired:
        p.kill()
    pv = [l for l in block if re.search(r"\binfo\b.*\bpv\b", l)]
    if not pv:
        return "(no pv)"
    m = re.search(r"score (mate|cp) (-?\d+)", pv[-1])
    return (f"{m.group(1)} {m.group(2)}" if m else "?") + "  |  " + pv[-1]


print(f"exe: {EXE}")
print(f"fen: {FEN}")
print(f"go depth {DEPTH}")
for name, opts in SETS.items():
    print(f"{name:30s} {run(opts)}")
