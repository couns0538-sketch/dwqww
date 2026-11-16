#!/usr/bin/env python3
"""Sum `nodes` over a rows run at fixed depth, for a given side-to-move option set.
Used to check the brief's known sums (plain build, S14, ucinewgame+isready before every go, Threads 1, Hash 16).
Usage: rows_sum.py EXE FILE DEPTH [S14|default]
"""
import subprocess, sys

exe, path, depth = sys.argv[1], sys.argv[2], int(sys.argv[3])
mode = sys.argv[4] if len(sys.argv) > 4 else "default"
S14 = [("LmrQuietBase", 93), ("LmrQuietDivisor", 205), ("LmrNoisyBase", 13), ("LmrNoisyDivisor", 333),
       ("LmrHistoryDivisor", 5643), ("NullMoveBase", 5), ("LmpBase", 8), ("HistoryPruneMultiplier", 2220),
       ("HistoryBonusQuadratic", 24), ("HistoryBonusLinear", 54), ("HistoryBonusMax", 2212),
       ("SingularDepth", 6), ("IirDepth", 2)]

fens = [l.strip() for l in open(path) if l.strip()]
total = 0
p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)
def send(c):
    p.stdin.write(c + "\n")
def drain_until(token):
    for line in p.stdout:
        if token in line:
            return line.rstrip()
    return None
send("uci"); drain_until("uciok")
send("setoption name Hash value 16"); send("setoption name Threads value 1")
send("setoption name OwnBook value false")
if mode == "S14":
    for k, v in S14:
        send(f"setoption name {k} value {v}")
    send("setoption name NonPawnCorrection value true")
send("isready"); drain_until("readyok")
for fen in fens:
    send("ucinewgame"); send("isready"); drain_until("readyok")
    send(f"position fen {fen}")
    send("isready"); drain_until("readyok")
    send(f"go depth {depth}")
    nodes = None
    saw_bestmove = False
    for line in p.stdout:
        if line.startswith("info depth"):
            f = line.split()
            nodes = int(f[f.index("nodes") + 1])
        if line.startswith("bestmove"):
            saw_bestmove = True
            break
    # Fail LOUDLY rather than counting a missing parse as zero (seat-19 measurement-integrity warning).
    if not saw_bestmove:
        raise SystemExit(f"ABORT: no bestmove for {fen} -- harness/engine protocol broken, nothing measured")
    if nodes is None:
        raise SystemExit(f"ABORT: no 'info depth ... nodes N' line for {fen} -- refusing to count it as 0")
    total += nodes
send("quit"); p.wait()
print(f"{path} depth {depth} mode {mode}: total nodes {total}")
