#!/usr/bin/env python3
"""hash_dependence.py EXE : is a MATE SCORE dependent on Hash size?

If a mate score changes when only the transposition-table size changes, the mate distance is being decided
by memory pressure rather than by the position. Test: for two proven positions, search to depth 20 at
Hash 1, 4, 16, 64, 256 MB, twice each, and report the mate number and the depth actually reached.

A mate number that varies with Hash is a finding; a mate number that is stable while only the reached depth
varies is not.
"""
import re
import shlex
import subprocess
import sys

EXE = sys.argv[1]
CASES = {
    "S-F8": "2b2knr/2qpp3/1r2n1pb/p4pP1/4PPQp/3P3P/PP1KB3/1qB3NR w - - 0 22",
    "S-F1": "8/8/1p6/8/p3p3/8/2Kpk3/8 w - - 0 1",
}
S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]


def run(fen, depth, hash_mb):
    p = subprocess.Popen(shlex.split(EXE), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)

    def until(w):
        for l in p.stdout:
            if l.strip() == w:
                return
    p.stdin.write("uci\n"); p.stdin.flush(); until("uciok")
    p.stdin.write("setoption name Threads value 1\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write(f"setoption name Hash value {hash_mb}\nisready\n"); p.stdin.flush(); until("readyok")
    for n, v in S14:
        p.stdin.write(f"setoption name {n} value {v}\n")
    p.stdin.write("isready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write("ucinewgame\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write(f"position fen {fen}\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write(f"go depth {depth}\n"); p.stdin.flush()
    last, reached, hf = None, 0, None
    while True:
        line = p.stdout.readline()
        if not line:
            break
        line = line.rstrip("\n")
        if line.startswith("info depth"):
            last = line
            d = re.search(r"depth (\d+)", line)
            if d:
                reached = int(d.group(1))
            h = re.search(r"hashfull (\d+)", line)
            if h:
                hf = int(h.group(1))
        if line.startswith("bestmove"):
            break
    p.stdin.write("quit\n"); p.stdin.flush()
    try:
        p.wait(timeout=10)
    except subprocess.TimeoutExpired:
        p.kill()
    m = re.search(r"score (cp|mate) (-?\d+)", last or "")
    return (f"{m.group(1)} {m.group(2)}" if m else "NO-SCORE"), reached, hf


for name, fen in CASES.items():
    print("=" * 70)
    print(name, fen)
    print(f"{'Hash MB':>8} {'run':>4} {'score':>10} {'reached':>8} {'hashfull':>9}")
    seen = {}
    for h in (1, 4, 16, 64, 256):
        for rep in (1, 2):
            sc, rd, hf = run(fen, 20, h)
            print(f"{h:>8} {rep:>4} {sc:>10} {rd:>8} {str(hf):>9}")
            seen.setdefault(sc, []).append(h)
    print(f"  distinct scores at depth 20: {sorted(seen)}")
    print(f"  -> {'HASH-DEPENDENT' if len(seen) > 1 else 'stable across Hash sizes'}")
