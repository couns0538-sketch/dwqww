#!/usr/bin/env python3
"""clamp_scope.py EXE : is the movestogo clamp-specific, or does every limit field treat 0 like absent?

S-C34 found `movestogo 0` is clamped to 1 by uci.cpp:172/241, which changes the time formula. The question that
bounds the finding: do OTHER limit fields have the same 0-vs-absent asymmetry? A grep shows `std::max(1, ...)` only
on movestogo, so the prediction is NO - but grep is not a measurement, and a field could still behave differently
for 0 through a different route.

Test each field by comparing "0 supplied" against "omitted":
  depth 0 vs absent      |  nodes 0 vs absent   |  movetime 0 vs absent  |  wtime/btime 0 vs absent
If only movestogo differs, the finding is specific and the advice is narrow. If others differ, it widens.
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
FEN = "rnb1kbnr/ppp1pppp/8/4q3/8/2N5/PPPP1PPP/R1BQKBNR w KQkq - 2 4"


def run(go):
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
    p.stdin.write(f"position fen {FEN}\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write(f"{go}\n"); p.stdin.flush()
    depth, best, errs = 0, None, []
    while True:
        line = p.stdout.readline()
        if not line:
            break
        s = line.rstrip("\n")
        if "unknown" in s.lower() or "invalid" in s.lower():
            errs.append(s)
        if s.startswith("info depth"):
            d = re.search(r"depth (\d+)", s)
            if d:
                depth = max(depth, int(d.group(1)))
        if s.startswith("bestmove"):
            best = s.split()[-1]
            break
    p.stdin.write("quit\n"); p.stdin.flush()
    try:
        p.wait(timeout=30)
    except subprocess.TimeoutExpired:
        p.kill()
    return depth, best, errs


PAIRS = [
    ("depth", "go depth 8", "go depth 0"),
    ("nodes", "go nodes 20000", "go nodes 0"),
    ("movetime", "go movetime 100", "go movetime 0"),
    ("clock", "go wtime 6000 btime 6000 winc 60 binc 60", "go wtime 6000 btime 6000 winc 60 binc 60 movestogo 0"),
]
print("### does the 0-vs-absent asymmetry affect fields other than movestogo?")
print(f"{'field':<10} {'supplied: depth/move':<28} {'zero: depth/move':<26} {'same?':>6}  errors")
for name, normal, zero in PAIRS:
    d1, b1, e1 = run(normal)
    d2, b2, e2 = run(zero)
    same = (d1 == d2 and b1 == b2)
    print(f"{name:<10} {str(d1)+' / '+str(b1):<28} {str(d2)+' / '+str(b2):<26} {str(same):>6}"
          + (f"  {e2[:1]}" if e2 else ""))
