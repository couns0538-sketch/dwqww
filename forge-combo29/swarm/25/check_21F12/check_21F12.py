#!/usr/bin/env python3
"""check_21F12.py PC_EXE BASE_EXE : does the PC build's drawn-root repair reach `searchmoves`?

SEAT 21's 21-F12, which I am checking:
  At halfmove counter 100, `go searchmoves e1e8 depth 4` on the PC build searches **8 nodes** and returns the mating
  move, where the BASE build answers **0 nodes** on the same line.
  The "no legal named move" case is UNCHANGED on the PC build (still `0000` plus the info line, 0 nodes).

WHY THIS IS A GOOD FINDING TO CHECK: it is a two-build difference on one command, so it can be verified without any
judgement about chess - either the node counts differ as stated or they do not. It also tests the PC's
FORGE_FIX_ROOT_DRAWN repair from a direction I had not: I established that the repair exists (my S-C19/C20 work read
`root_drawn`), but not that it reaches the `searchmoves` restriction path.

MY CHECK: both builds, the same FENs and commands, fresh process each, comparing nodes / bestmove / info lines.
Cases:
  A  halfmove 100, one legal searchmove that MATES  -> PC should search > 0, base should be 0
  B  halfmove 100, a searchmove that is NOT legal    -> both should answer 0000 + info line, 0 nodes
  C  halfmove 100, unrestricted                      -> the drawn-root case itself
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
PC_EXE, BASE_EXE = sys.argv[1], sys.argv[2]

# a board where white has a mate in 1 (a1a8) and the halfmove counter is 100: drawn-root territory
FEN100 = "6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 100 1"


def run(exe, fen, go, pc):
    p = subprocess.Popen(shlex.split(exe), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
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
    p.stdin.write(f"{go}\n"); p.stdin.flush()
    lines, best = [], None
    while True:
        line = p.stdout.readline()
        if not line:
            break
        s = line.rstrip("\n")
        if s.startswith("info"):
            lines.append(s)
        if s.startswith("bestmove"):
            best = s.split()[-1]
            break
    p.stdin.write("quit\n"); p.stdin.flush()
    try:
        p.wait(timeout=20)
    except subprocess.TimeoutExpired:
        p.kill()
    nodes = 0
    score = "?"
    for l in reversed(lines):
        if l.startswith("info depth"):
            n = re.search(r"nodes (\d+)", l)
            if n:
                nodes = int(n.group(1))
            m = re.search(r"score (cp|mate) (-?\d+)", l)
            if m:
                score = m.group(0)
            break
    return nodes, best, score, len(lines)


CASES = [
    ("A halfmove 100, searchmoves e1e8 (a legal mate-in-1? check)", FEN100, "go searchmoves e1e8 depth 4"),
    ("B halfmove 100, searchmoves a7a8 (not legal for white here)", FEN100, "go searchmoves a7a8 depth 4"),
    ("C halfmove 100, unrestricted", FEN100, "go depth 4"),
    ("D halfmove 0, searchmoves a1a8 (the mate, no draw)", "6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 0 1",
     "go searchmoves a1a8 depth 4"),
]
print("### 21-F12 check: does the PC drawn-root repair reach `searchmoves`?")
print(f"PC   {PC_EXE}")
print(f"BASE {BASE_EXE}")
print()
print(f"{'case':<58} {'build':>5} {'nodes':>7} {'bestmove':>9} {'score':>12} {'infos':>6}")
for name, fen, go in CASES:
    for label, exe, pc in (("PC", PC_EXE, True), ("base", BASE_EXE, False)):
        nodes, best, score, n = run(exe, fen, go, pc)
        print(f"{name[:58]:<58} {label:>5} {nodes:>7} {str(best):>9} {score:>12} {n:>6}")
    print()
