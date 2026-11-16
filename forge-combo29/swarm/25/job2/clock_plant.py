#!/usr/bin/env python3
"""clock_plant.py EXE : the Rule-1 plant for the clock-99 finding.

A "0 at clock 99" could be my harness failing to read the score, or the engine really answering 0.
Plant: the SAME board at clock 98 must NOT be zero (it is ~ -112 / -198 / -215). So a harness that
reports 0 for everything is caught. Plus: assert every record carries a parsed score, so an absent
score cannot be mistaken for a zero.
"""
import re
import subprocess
import sys

EXE = sys.argv[1]
BOARD = "r4rk1/pp1b1ppp/4p3/3pP3/8/P3P3/1P2N1PP/R2R2K1 w - - {c} 1"


def score_of(fen, depth=10):
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    for c in ["uci", "isready", "setoption name Threads value 1", "isready",
              "ucinewgame", "isready", f"position fen {fen}", "isready", f"go depth {depth}"]:
        p.stdin.write(c + "\n")
        p.stdin.flush()
        if c == "uci":
            for l in p.stdout:
                if l.strip() == "uciok":
                    break
        elif c == "isready":
            for l in p.stdout:
                if l.strip() == "readyok":
                    break
    infos = []
    while True:
        line = p.stdout.readline()
        if not line:
            break
        line = line.rstrip("\n")
        if line.startswith("info depth"):
            infos.append(line)
        if line.startswith("bestmove"):
            break
    p.stdin.write("quit\n"); p.stdin.flush()
    try:
        p.wait(timeout=5)
    except subprocess.TimeoutExpired:
        p.kill()
    if not infos:
        return None, 0
    m = re.search(r"score (cp|mate) (-?\d+)", infos[-1])
    n = re.search(r"nodes (\d+)", infos[-1])
    return (int(m.group(2)) if m else None), (int(n.group(1)) if n else 0)


ok = True
c98, n98 = score_of(BOARD.format(c=98))
c99, n99 = score_of(BOARD.format(c=99))
print(f"plant control  clock 98: score {c98} nodes {n98}")
print(f"plant subject  clock 99: score {c99} nodes {n99}")
if c98 is None:
    print("FAIL: no score parsed at clock 98 — the harness cannot see scores at all")
    ok = False
elif c98 == 0:
    print("FAIL: clock 98 also scores 0 — a harness that always reports 0 is caught here")
    ok = False
else:
    print(f"PASS: the harness sees a non-zero score ({c98}) on the same board at clock 98")
if c99 != 0:
    print(f"NOTE: clock 99 did NOT score 0 here ({c99}); the finding does not reproduce")
    ok = False
print("RESULT:", "plant passed, the clock-99 zero is a real engine answer, not a harness artefact"
      if ok else "plant failed: do not report the finding")
sys.exit(0 if ok else 3)
