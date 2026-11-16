#!/usr/bin/env python3
"""experiment3.py : WHY does the root not see the winning reset move?

Experiment 2 established: at clock 99 on board A, all 9 clock-resetting moves keep the game alive with scores
+166..+823 (searched with the clock zeroed, so the fifty-move rule cannot interfere), yet the engine answers
`cp 0` with a 1-ply PV, at every depth 1..6.

`[DBG ROOT ITER SEARCHED] depth=1 score=0 pv_len=1` says the ROOT searched exactly one move. That is the
signature of `root_candidates` being reduced to ONE entry, or of the first root move scoring 0 and every other
root move failing high/low so it is never recorded.

Decisive check available WITHOUT more instrumentation: ask the engine to search ONLY the winning reset move,
via `searchmoves`. If `go depth 8 searchmoves d1d5` returns +823-ish instead of 0, then the move is fine and
the ROOT never got to it (ordering/cutoff problem). If it returns 0, the move itself is being scored 0 at
clock 99 and the fault is in the search below the root.
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
EXE = sys.argv[1]
A = "r4rk1/pp1b1ppp/4p3/3pP3/8/P3P3/1P2N1PP/R2R2K1 w - - 99 1"


def run(fen, go):
    p = subprocess.Popen(shlex.split(EXE), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1)

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
    p.stdin.write(f"{go}\n"); p.stdin.flush()
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
    last = infos[-1] if infos else ""
    m = re.search(r"score (cp|mate) (-?\d+)", last)
    n = re.search(r"nodes (\d+)", last)
    toks = last.split()
    pv = toks[toks.index("pv") + 1:] if "pv" in toks else []
    return ((m.group(1), int(m.group(2))) if m else None), (int(n.group(1)) if n else 0), best, len(pv)


print("unrestricted search at clock 99:")
for d in (1, 2, 4, 8):
    print(f"  go depth {d:<2} ->", run(A, f"go depth {d}"))

print()
print("search RESTRICTED to each reset move with `searchmoves` (depth 8):")
for mv in ("d1d5", "b2b4", "h2h4", "e3e4"):
    print(f"  searchmoves {mv} ->", run(A, f"go depth 8 searchmoves {mv}"))

print()
print("for contrast, unrestricted search on the SAME board at clock 0:")
A0 = A.replace(" 99 1", " 0 1")
print("  go depth 8 ->", run(A0, "go depth 8"))
