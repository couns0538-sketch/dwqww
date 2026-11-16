#!/usr/bin/env python3
"""check_11_sf6.py EXE LABEL : verify seat 11's ladder before withdrawing my own S-F6.

Seat 11's argument: UCI defines `score mate y` as mate in y moves for the side to move, so y=0 means
"already mated", and `bestmove 0000` is the only sensible reply. Therefore a checkmated root answering
`mate 0` / `0000` / 0 nodes is NOT a fault, and my S-F6 should be withdrawn.

I verify the ladder on my own builds rather than accepting the summary. The ladder should be:
  checkmated root      -> mate 0   / 0000        / 0 nodes
  mate in 1 available  -> mate 1   / real move   / >0 nodes
  stalemated root      -> cp 0     / 0000
  dead draw (KvK)      -> cp 0     / a move
  KQ vs K (won)        -> a large positive cp / a move
If that is what I see, the ladder is coherent: the engine distinguishes "already over" (mate 0 + 0000) from
"mate available" (mate N + a move), which is exactly the UCI reading. Then S-F6 is a non-defect.
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
LABEL = sys.argv[2]
CASES = [
    ("checkmated root", "8/8/Q7/8/8/K7/8/k1Q5 b - - 0 1"),
    ("mate in 1 available", "6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 0 1"),
    ("stalemated root", "7k/5Q2/6K1/8/8/8/8/8 b - - 0 1"),
    ("dead draw KvK", "8/8/4k3/8/8/4K3/8/8 w - - 0 1"),
    ("KQ vs K (won)", "8/8/8/8/3k4/8/8/K1Q5 w - - 0 1"),
]


def run(fen):
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
    p.stdin.write("go depth 5\n"); p.stdin.flush()
    lines, best = [], None
    while True:
        line = p.stdout.readline()
        if not line:
            break
        s = line.rstrip("\n")
        if s.startswith("info depth"):
            lines.append(s)
        if s.startswith("bestmove"):
            best = s.split()[-1]
            break
    p.stdin.write("quit\n"); p.stdin.flush()
    try:
        p.wait(timeout=15)
    except subprocess.TimeoutExpired:
        p.kill()
    score = "?"
    nodes = 0
    if lines:
        m = re.search(r"score (cp|mate) (-?\d+)", lines[-1])
        score = m.group(0) if m else "?"
        n = re.search(r"nodes (\d+)", lines[-1])
        nodes = int(n.group(1)) if n else 0
    return score, best, nodes, len(lines)


print(f"### seat 11's ladder, verified — {LABEL} (PC20, Threads 1, Hash 16, go depth 5)")
print()
print(f"{'case':<24} {'score':>12} {'bestmove':>9} {'nodes':>7} {'infos':>6}   reading")
for name, fen in CASES:
    score, best, nodes, infos = run(fen)
    print(f"{name:<24} {score:>12} {str(best):>9} {nodes:>7} {infos:>6}")

print()
print("Expected per seat 11 / UCI: checkmated -> mate 0 + 0000 + 0 nodes; mate-in-1 -> mate 1 + a real move;")
print("stalemate -> cp 0 + 0000; dead draw -> cp 0; KQvK -> large positive.")
