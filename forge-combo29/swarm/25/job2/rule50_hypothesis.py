#!/usr/bin/env python3
"""rule50_hypothesis.py EXE : which option/mechanism makes clock 99 score 0?

Three hypotheses, each tested by toggling exactly one thing on the SAME board:
  H1  the root/leaf fifty-move test          -> test clock 99 vs clock 100 vs clock 101
  H2  the evaluation damping option          -> test `setoption name EvalRule50Damp value true/false`
  H3  the search damping (depth-dependent)   -> test `go depth 16` with hash cleared between
A result that stays 0 under every toggle is not explained by that toggle; a result that changes names
the mechanism.
"""
import re
import subprocess
import sys

EXE = sys.argv[1]
BOARD = "r4rk1/pp1b1ppp/4p3/3pP3/8/P3P3/1P2N1PP/R2R2K1 w - - {c} 1"


def run(fen, go="go depth 10", options=()):
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)

    def until(word):
        for line in p.stdout:
            if line.strip() == word:
                return

    p.stdin.write("uci\n"); p.stdin.flush(); until("uciok")
    p.stdin.write("setoption name Threads value 1\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write("setoption name Hash value 16\nisready\n"); p.stdin.flush(); until("readyok")
    for opt in options:
        p.stdin.write(f"setoption name {opt}\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write("ucinewgame\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write(f"position fen {fen}\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write(go + "\n"); p.stdin.flush()
    infos, best = [], None
    while True:
        line = p.stdout.readline()
        if not line:
            break
        line = line.rstrip("\n")
        if line.startswith("info depth"):
            infos.append(line)
        if line.startswith("bestmove"):
            best = line
            break
    p.stdin.write("quit\n"); p.stdin.flush()
    try:
        p.wait(timeout=5)
    except subprocess.TimeoutExpired:
        p.kill()
    if not infos:
        return None, None, 0
    m = re.search(r"score (cp|mate) (-?\d+)", infos[-1])
    n = re.search(r"nodes (\d+)", infos[-1])
    return (int(m.group(2)) if m else None), (best.split()[-1] if best else None), \
           (int(n.group(1)) if n else 0)


# PLANT GUARD: a `d2d4`-only answer to every clock value would mean the engine searched STARTPOS, not
# the board I sent (a `ucinewgame` placed after `position fen` does exactly that). Assert the first
# probe does not return the startpos-only bestmove set, and fail loudly if it does.
_PROBE = run(BOARD.format(c=0))
print(f"guard: clock 0 on the test board -> score {_PROBE[0]} bestmove {_PROBE[1]}")
if _PROBE[1] in ("d2d4", "e2e4", "g1f3", "c2c4") and (BOARD.format(c=0).split()[1] == "r4rk1/pp1b1ppp/4p3/3pP3/8/P3P3/1P2N1PP/R2R2K1"):
    print("GUARD FAILED: the engine answered with a startpos move on a non-startpos board.")
    print("  This means the position was not set (command order bug). No results are valid.")
    sys.exit(3)
print()


print("H1: does the clock value itself decide it?")
for clock in (95, 97, 98, 99, 100, 101):
    sc, mv, nd = run(BOARD.format(c=clock))
    print(f"   clock {clock:>3}: score {str(sc):>6} nodes {nd:>6} bestmove {mv}")

print()
print("H2: does the EvalRule50Damp option change it?")
for opt in ([], ["EvalRule50Damp value true"], ["EvalRule50Damp value false"]):
    sc, mv, nd = run(BOARD.format(c=99), options=opt)
    print(f"   clock 99 with {opt or 'default options'}: score {sc} nodes {nd} bestmove {mv}")

print()
print("H3: is it depth dependent at clock 99?")
for d in (1, 6, 10, 20, 30):
    sc, mv, nd = run(BOARD.format(c=99), go=f"go depth {d}")
    print(f"   clock 99 go depth {d:>2}: score {sc} nodes {nd} bestmove {mv}")

print()
print("H4: is it present with UseNNUE false (i.e. is the net involved)?")
for opt in (["UseNNUE value false"], ["UseNNUE value true"]):
    sc, mv, nd = run(BOARD.format(c=99), options=opt)
    print(f"   clock 99 with {opt[0]}: score {sc} nodes {nd} bestmove {mv}")
