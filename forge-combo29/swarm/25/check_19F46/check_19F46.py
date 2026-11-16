#!/usr/bin/env python3
"""check_19F46.py EXE : independent check of seat 19's 19-F46.

Claim: `go nodes N` UNDERSHOOTS N by a median of -32% (range -51.9%..-0.8%), deterministically, because an
interrupted iteration is discarded; and `go softnodes N` OVERSHOOTS (median +21.9%). The two modes sit on
opposite sides of N, and softnodes reached one ply deeper in all 18 cells.

My check, written from the claim, PC20 / Threads 1 / Hash 16, on my own position set:
  * for N in {20000, 50000, 250000}: the nodes REPORTED on the final info line vs N (the ratio)
  * the same for `go softnodes N`
  * the depth each reached
Note on what "undershoot" means here: the reported node count is the count on the LAST COMPLETED iteration, so a
ratio below 1 is expected for `go nodes` if the budget is hit mid-iteration and the partial is discarded. I check
whether that is what the numbers show, rather than assuming it.
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
FENS = sys.argv[2]
LIMIT = int(sys.argv[3]) if len(sys.argv) > 3 else 6


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
    last, depth = None, 0
    while True:
        line = p.stdout.readline()
        if not line:
            break
        s = line.rstrip("\n")
        if s.startswith("info depth"):
            last = s
            d = re.search(r"depth (\d+)", s)
            if d:
                depth = max(depth, int(d.group(1)))
        if s.startswith("bestmove"):
            break
    p.stdin.write("quit\n"); p.stdin.flush()
    try:
        p.wait(timeout=20)
    except subprocess.TimeoutExpired:
        p.kill()
    n = re.search(r"nodes (\d+)", last or "")
    return (int(n.group(1)) if n else 0), depth


fens = [l.split(";")[0].strip() for l in open(FENS) if l.strip()][:LIMIT]
print("### check of 19-F46: `go nodes` vs `go softnodes` around N")
print("PC r15/PC20, Threads 1, Hash 16")
print()
print(f"{'position':<44} {'N':>7} {'nodes':>8} {'ratio':>7} {'dep':>4} | {'soft':>8} {'ratio':>7} {'dep':>4}")
ratios_hard, ratios_soft, deeper = [], [], 0
for fen in fens:
    for N in (20000, 50000, 250000):
        nh, dh = run(fen, f"go nodes {N}")
        ns, ds = run(fen, f"go softnodes {N}")
        rh = nh / N if N else 0
        rs = ns / N if N else 0
        ratios_hard.append(rh)
        ratios_soft.append(rs)
        deeper += (ds > dh)
        print(f"{fen[:44]:<44} {N:>7} {nh:>8} {rh:>7.2f} {dh:>4} | {ns:>8} {rs:>7.2f} {ds:>4}")

import statistics
print()
print(f"`go nodes`     ratio: median {statistics.median(ratios_hard):.2f}, "
      f"min {min(ratios_hard):.2f}, max {max(ratios_hard):.2f}")
print(f"`go softnodes` ratio: median {statistics.median(ratios_soft):.2f}, "
      f"min {min(ratios_soft):.2f}, max {max(ratios_soft):.2f}")
print(f"cells where softnodes reached a deeper ply: {deeper}/{len(ratios_hard)}")
print()
print("Seat 19 claims: hard median -32% (0.68), soft median +21.9% (1.219), soft deeper in 18/18.")
