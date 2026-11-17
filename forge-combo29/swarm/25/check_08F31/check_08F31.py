#!/usr/bin/env python3
"""check_08F31.py EXE FENS : does a clocked search MISS a mate that a D+4 search finds?

SEAT 08's 08-F31, which I am checking:
  PC r15, PC20, Threads 1, Hash 16, 6 s + 0.06 clock, 30 boards per class.
  SPARSE class (<= 12 pieces): 10 of 27 boards (37 %) have a MATE the clocked search has not found - `cp ...` at the
  clock's own depth D, versus `mate ...` at depth D+4.
  FULL-MATERIAL class (>= 20 pieces): 0 of 30 for mate.
  So the sparse error expresses as a MATE APPEARING at greater depth, not as a cp magnitude - quoting only the cp
  gap would understate it.

MY CHECK, on the same principle but my own harness and my own board selection:
  * take the 16 G positions seat 13 used, which I already have, and classify by piece count
  * for each: run the match clock (6 s + 0.06) -> note score and depth D
  * then run `go depth D+4` -> note whether a MATE appears where the clock said cp
  * report per board and per class
This tests the MECHANISM (does a deeper search find mates the clock does not) rather than seat 08's exact rate,
since I do not have their 60 boards. A mechanism that reproduces on my boards corroborates theirs; one that does
not leaves their rate unconfirmed but their mechanism untested.
"""
import re
import shlex
import subprocess
import sys
import time

import chess

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]
PC20_EXTRA = [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
              ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]
EXE = sys.argv[1]
FENS = sys.argv[2]
LIMIT = int(sys.argv[3]) if len(sys.argv) > 3 else 16


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
    for n, v in S14 + PC20_EXTRA:
        p.stdin.write(f"setoption name {n} value {v}\n")
    p.stdin.write("isready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write("ucinewgame\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write(f"position fen {fen}\nisready\n"); p.stdin.flush(); until("readyok")
    t0 = time.monotonic()
    p.stdin.write(f"{go}\n"); p.stdin.flush()
    last = None
    while True:
        line = p.stdout.readline()
        if not line:
            break
        s = line.rstrip("\n")
        if s.startswith("info depth") and " pv " in s:
            last = s
        if s.startswith("bestmove"):
            break
    ms = (time.monotonic() - t0) * 1000.0
    p.stdin.write("quit\n"); p.stdin.flush()
    try:
        p.wait(timeout=180)
    except subprocess.TimeoutExpired:
        p.kill()
    score, depth, kind = "?", 0, None
    if last:
        m = re.search(r"score (cp|mate) (-?\d+)", last)
        if m:
            score = m.group(0)
            kind = m.group(1)
        d = re.search(r"depth (\d+)", last)
        depth = int(d.group(1)) if d else 0
    return score, depth, kind, round(ms)


fens = [l.split(";")[0].strip() for l in open(FENS) if l.strip()][:LIMIT]
print("### 08-F31 mechanism: does a clocked search miss mates a D+4 search finds?")
print(f"clock: go wtime 6000 btime 6000 winc 60 binc 60 | reference: go depth D+4 | PC20, Threads 1, Hash 16")
print()
print(f"{'#':>3} {'pieces':>6} {'class':>8} {'clock score':>13} {'D':>3} {'D+4 score':>13} {'mate appeared?':>15}")
sparse_tot = sparse_mate = full_tot = full_mate = 0
for idx, fen in enumerate(fens, 1):
    b = chess.Board(fen)
    pieces = len(b.piece_map())
    cls = "sparse" if pieces <= 12 else ("full" if pieces >= 20 else "mid")
    s1, d1, k1, ms = run(fen, "go wtime 6000 btime 6000 winc 60 binc 60")
    s2, d2, k2, _ = run(fen, f"go depth {d1 + 4}")
    appeared = (k1 == "cp" and k2 == "mate")
    if cls == "sparse":
        sparse_tot += 1
        sparse_mate += appeared
    elif cls == "full":
        full_tot += 1
        full_mate += appeared
    print(f"{idx:>3} {pieces:>6} {cls:>8} {s1:>13} {d1:>3} {s2:>13} {str(appeared):>15}")

print()
print(f"SPARSE (<=12 pieces): {sparse_mate} of {sparse_tot} boards had a mate appear at D+4")
print(f"FULL   (>=20 pieces): {full_mate} of {full_tot} boards had a mate appear at D+4")
print()
print("seat 08 claim: sparse 10 of 27 (37 %), full 0 of 30.")
