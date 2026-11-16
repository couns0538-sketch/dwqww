#!/usr/bin/env python3
"""ownbook_check.py EXE OUT.txt : is any of my recorded work contaminated by the default OwnBook true?

Part A: 30 G positions at depth 10 WITH the default (no OwnBook line) and WITH OwnBook false; compare
        bestmove and the depth-10 score.
Part B: 20 G positions' `eval` lines with and without OwnBook false.
Part C: try to make the book answer at all (startpos and a few early-opening FENs), reporting any
        `info string book move` line.
"""
import re
import subprocess
import sys
import time

import chess

EXE, OUT = sys.argv[1], sys.argv[2]
S14 = [("LmrQuietBase", 93), ("LmrQuietDivisor", 205), ("LmrNoisyBase", 13), ("LmrNoisyDivisor", 333),
       ("LmrHistoryDivisor", 5643), ("NullMoveBase", 5), ("LmpBase", 8), ("HistoryPruneMultiplier", 2220),
       ("HistoryBonusQuadratic", 24), ("HistoryBonusLinear", 54), ("HistoryBonusMax", 2212),
       ("SingularDepth", 6), ("IirDepth", 2), ("NonPawnCorrection", "true")]


def send_all(p, script):
    for c in script:
        p.stdin.write(c + "\n")
        p.stdin.flush()


def search(fen, ownbook_false, depth=10):
    setup = ["uci", "isready", "setoption name Threads value 1", "isready",
             "setoption name Hash value 16", "isready"]
    if ownbook_false:
        setup += ["setoption name OwnBook value false", "isready"]
    for n, v in S14:
        setup += [f"setoption name {n} value {v}", "isready"]
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    send_all(p, setup + [f"position fen {fen}", "isready", f"go depth {depth}"])
    lines = []
    deadline = time.monotonic() + 120
    while time.monotonic() < deadline:
        l = p.stdout.readline()
        if not l:
            break
        lines.append(l.rstrip("\n"))
        if l.startswith("bestmove"):
            break
    try:
        p.stdin.write("quit\n"); p.stdin.flush(); p.wait(timeout=5)
    except Exception:
        p.kill()
    best = next((l.split()[1] for l in lines if l.startswith("bestmove")), None)
    score = None
    for l in lines:
        m = re.match(rf"^info depth {depth} .*score (cp|mate) (-?\d+)", l)
        if m:
            score = (m.group(1), int(m.group(2)))
    book = [l for l in lines if "book move" in l]
    return best, score, book


def ev(fen, ownbook_false):
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    setup = ["uci", "isready"]
    if ownbook_false:
        setup += ["setoption name OwnBook value false", "isready"]
    send_all(p, setup + [f"position fen {fen}", "isready", "eval", "isready", "quit"])
    lines = []
    while True:
        l = p.stdout.readline()
        if not l:
            break
        lines.append(l.rstrip("\n"))
        if l.startswith("info string eval"):
            break
    try:
        p.kill()
    except Exception:
        pass
    return next((l for l in lines if l.startswith("info string eval")), None)


fens = [l.strip() for l in open("/agent/repos/dwqww/forge-combo29/swarm/16/job3/set_G.epd") if l.strip()]
out = []
same_bm = same_score = 0
for fen in fens[:30]:
    a = search(fen, False)
    b = search(fen, True)
    if a[0] == b[0]:
        same_bm += 1
    if a[1] == b[1]:
        same_score += 1
    out.append(f"A {fen}\n  default  {a[0]} {a[1]} book={a[2]}\n  OwnBook false {b[0]} {b[1]} book={b[2]}")
out.append(f"\nPART A: 30 positions, bestmove same {same_bm}/30, score same {same_score}/30")

same_ev = 0
for fen in fens[:20]:
    a, b = ev(fen, False), ev(fen, True)
    if a == b:
        same_ev += 1
out.append(f"\nPART B: 20 positions, eval line identical {same_ev}/20")

out.append("\nPART C: can the book answer at all?")
tries = ["rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
         "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1",
         "rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq e6 0 2"]
for fen in tries:
    res = search(fen, False)
    out.append(f"  {fen} -> {res[0]} {res[1]} book={res[2]}")
text = "\n".join(out) + "\n"
print(text)
with open(OUT, "w") as fh:
    fh.write(text)
