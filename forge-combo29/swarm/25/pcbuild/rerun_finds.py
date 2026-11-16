#!/usr/bin/env python3
"""rerun_finds.py EXE LABEL : re-runs every find of mine on ONE build/settings combination.

LABEL names the build+settings for the finding lines, e.g. "PC r15 / PC20" or "base / S14".
Threads 1 always. Checks, in order:
  F1  S-F1  depth 12 on 8/8/1p6/8/p3p3/8/2Kpk3/8 w        -> base gave mate -12 (wrong; truth -4)
  F8  S-F8  depth 12 on 2b2knr/...NR w - - 0 22           -> base gave mate -9  (wrong; truth -7 at Hash64)
  F3  S-F3  clock 98 vs clock 99 on r4rk1/pp1b1ppp/...    -> base: 98 normal, 99 = cp 0
  F6  S-F6  checkmated root                               -> base: score mate 0
  F7  S-F7  terminal root, go nodes 100                   -> base: 64 info lines at 0 nodes
Each result is printed as PRESENT (fault still there) or GONE (repaired) with the raw numbers.
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
PC20_EXTRA = [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
              ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]

EXE = sys.argv[1]
LABEL = sys.argv[2]
MODE = sys.argv[3] if len(sys.argv) > 3 else "PC20"   # PC20 | S14
HASH = int(sys.argv[4]) if len(sys.argv) > 4 else 16

EXTRA = PC20_EXTRA if MODE == "PC20" else []


def run(position_cmd, go):
    p = subprocess.Popen(shlex.split(EXE), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)

    def until(w):
        for l in p.stdout:
            if l.strip() == w:
                return
    p.stdin.write("uci\n"); p.stdin.flush(); until("uciok")
    p.stdin.write("setoption name Threads value 1\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write(f"setoption name Hash value {HASH}\nisready\n"); p.stdin.flush(); until("readyok")
    for n, v in S14 + EXTRA:
        p.stdin.write(f"setoption name {n} value {v}\n")
    p.stdin.write("isready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write("ucinewgame\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write(f"{position_cmd}\nisready\n"); p.stdin.flush(); until("readyok")
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
            best = s.split()[-1]
            break
    p.stdin.write("quit\n"); p.stdin.flush()
    try:
        p.wait(timeout=10)
    except subprocess.TimeoutExpired:
        p.kill()
    return infos, best


def summary(infos):
    if not infos:
        return None, 0, 0, 0
    m = re.search(r"score (cp|mate) (-?\d+)", infos[-1])
    nodes = re.search(r"nodes (\d+)", infos[-1])
    depth = re.search(r"depth (\d+)", infos[-1])
    return ((m.group(1), int(m.group(2))) if m else None,
            int(depth.group(1)) if depth else 0,
            int(nodes.group(1)) if nodes else 0,
            len(infos))


print(f"### {LABEL}  ({MODE}, Threads 1, Hash {HASH})")

# S-F1
infos, best = run("position fen 8/8/1p6/8/p3p3/8/2Kpk3/8 w - - 0 1", "go depth 12")
sc, d, n, k = summary(infos)
verdict = "GONE (repaired)" if sc != ("mate", -12) else "PRESENT"
print(f"S-F1 depth12: {sc} depth {d} nodes {n} best {best} -> {verdict}  [base said mate -12, truth mate -4]")

# S-F8
infos, best = run("position fen 2b2knr/2qpp3/1r2n1pb/p4pP1/4PPQp/3P3P/PP1KB3/1qB3NR w - - 0 22", "go depth 12")
sc, d, n, k = summary(infos)
verdict = "GONE (repaired)" if sc != ("mate", -9) else "PRESENT"
print(f"S-F8 depth12: {sc} depth {d} nodes {n} best {best} -> {verdict}  [base said mate -9]")

# S-F3
for clock in (98, 99):
    infos, best = run(f"position fen r4rk1/pp1b1ppp/4p3/3pP3/8/P3P3/1P2N1PP/R2R2K1 w - - {clock} 1", "go depth 10")
    sc, d, n, k = summary(infos)
    print(f"S-F3 clock {clock}: {sc} depth {d} nodes {n} best {best}")

# S-F6
infos, best = run("position fen 8/8/Q7/8/8/K7/8/k1Q5 b - - 0 1", "go depth 5")
sc, d, n, k = summary(infos)
verdict = "GONE (repaired)" if sc != ("mate", 0) else "PRESENT"
print(f"S-F6 checkmated root: {sc} best {best} -> {verdict}  [base said mate 0]")

# S-F7
infos, best = run("position fen 8/8/Q7/8/8/K7/8/k1Q5 b - - 0 1", "go nodes 100")
sc, d, n, k = summary(infos)
verdict = "PRESENT" if k >= 60 else "GONE (repaired)"
print(f"S-F7 go nodes 100 on terminal root: {k} info lines, depth {d}, nodes {n} -> {verdict}  [base emitted 64]")
