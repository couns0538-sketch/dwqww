#!/usr/bin/env python3
"""mate0_probe.py EXE : quantify the `score mate 0` answer on a checkmated root.

At a checkmated root the engine emits `info depth N ... score mate 0 ... nodes 0` for every depth and
only stops at the search limit, instead of emitting one line and stopping. This measures:
  - how many info lines are emitted for go depth 5 / go nodes 100 / go movetime 50
  - whether the score is reported as `mate 0` (a mate score of zero, which is not a legal claim)
  - whether bestmove is 0000
Also the control: a STALEMATED root (also terminal, but not mate) - what score does it report?
"""
import re
import subprocess
import sys

EXE = sys.argv[1]
CASE = {
    "checkmated root": "8/8/Q7/8/8/K7/8/k1Q5 b - - 0 1",
    "stalemated root": None,  # filled from the generated file below
}

for line in open("/agent/repos/dwqww/forge-combo29/swarm/25/job3/stale_roots.fens"):
    CASE["stalemated root"] = line.strip()
    break


def run(fen, go):
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)

    def until(w):
        for l in p.stdout:
            if l.strip() == w:
                return
    p.stdin.write("uci\n"); p.stdin.flush(); until("uciok")
    p.stdin.write("isready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write("ucinewgame\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write(f"position fen {fen}\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write(go + "\n"); p.stdin.flush()
    infos, best, san = [], None, 0
    while True:
        line = p.stdout.readline()
        if not line:
            break
        line = line.rstrip("\n")
        if line.startswith("info depth"):
            infos.append(line)
        if re.search(r"Sanitizer|runtime error:", line):
            san += 1
        if line.startswith("bestmove"):
            best = line
            break
    p.stdin.write("quit\n"); p.stdin.flush()
    try:
        p.wait(timeout=10)
    except subprocess.TimeoutExpired:
        p.kill()
    return infos, best, san


for name, fen in CASE.items():
    print("=" * 70)
    print(f"{name}: {fen}")
    for go in ("go depth 5", "go nodes 100", "go movetime 50"):
        infos, best, san = run(fen, go)
        scores = {re.search(r"score \S+ -?\d+", l).group(0) for l in infos
                  if re.search(r"score \S+ -?\d+", l)}
        depths = [int(re.search(r"depth (\d+)", l).group(1)) for l in infos]
        print(f"  {go:<16} info_lines={len(infos):>3} depth {min(depths) if depths else '-'}"
              f"..{max(depths) if depths else '-'}  scores={sorted(scores)}  "
              f"{best}  sanitizer={san}")
