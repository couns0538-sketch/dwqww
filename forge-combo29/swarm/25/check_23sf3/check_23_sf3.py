#!/usr/bin/env python3
"""check_23_sf3.py EXE : is my S-F3's clock-99 onset a SEARCH-HORIZON effect rather than a coded boundary?

SEAT 23's REFUTATION of my S-F3 mechanism, which I am testing:
  On a won K+R vs K board, cp 0 first appears at counter 92, and 98 is already cp 0 - so nothing is one ply early
  against my own 98. A depth sweep gives first-cp-0 counters of 95 / 92 / 91 / 89 / 89 at depths 6 / 8 / 10 / 12 / 14,
  tracking roughly 100 - depth. So the boundary is the SEARCH HORIZON meeting the 100th half-move, not a hard-coded
  test at 99. Onset is board-dependent: 92 on their board, 99 on mine.

WHY THIS MATTERS DESPITE my S-F3 already being reclassified as not-a-defect: it changes the MECHANISM. If the onset on
my board moves with depth, then my "exactly 99" was a depth-10 observation of a horizon, not a property of the code.
That is a correction to my own explanation, which is worth recording either way.

THE TEST on MY OWN BOARD (r4rk1/pp1b1ppp/4p3/3pP3/8/P3P3/1P2N1PP/R2R2K1 w):
  for depth D in 6, 8, 10, 12, 14: sweep the counter and find the FIRST counter that scores cp 0.
  If the first-zero counter falls as depth rises, roughly 100 - D, seat 23 is right and my 99 is a horizon point.
  If it stays pinned at 99 for every depth, my original reading stands.
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
BOARD = "r4rk1/pp1b1ppp/4p3/3pP3/8/P3P3/1P2N1PP/R2R2K1 w - - {c} 1"


def run(fen, depth):
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
    p.stdin.write(f"go depth {depth}\n"); p.stdin.flush()
    last = None
    while True:
        line = p.stdout.readline()
        if not line:
            break
        s = line.rstrip("\n")
        if s.startswith("info depth"):
            last = s
        if s.startswith("bestmove"):
            break
    p.stdin.write("quit\n"); p.stdin.flush()
    try:
        p.wait(timeout=20)
    except subprocess.TimeoutExpired:
        p.kill()
    m = re.search(r"score (cp|mate) (-?\d+)", last or "")
    nodes = re.search(r"nodes (\d+)", last or "")
    return (m.group(0) if m else "?"), (int(nodes.group(1)) if nodes else 0)


print("### seat 23's horizon claim, tested on MY board")
print(f"board: {BOARD.format(c='<c>')}")
print(f"predict: first-cp-0 counter ~ 100 - depth  (seat 23: 95/92/91/89/89 at depths 6/8/10/12/14)")
print()
print(f"{'depth':>6} {'first cp0 at counter':>22} {'100-depth':>10}  {'near?':>6}")
for depth in (6, 8, 10, 12, 14):
    first = None
    detail = {}
    for c in range(80, 101):
        score, nodes = run(BOARD.format(c=c), depth)
        detail[c] = (score, nodes)
        if first is None and score == "score cp 0":
            first = c
            break
    pred = 100 - depth
    near = abs(first - pred) <= 3 if first is not None else False
    print(f"{depth:>6} {str(first):>22} {pred:>10}  {str(near):>6}")
    if first is not None:
        # show the two counters around the onset, so the boundary is visible not just asserted
        for c in (first - 1, first):
            if c in detail:
                print(f"          counter {c}: {detail[c][0]} ({detail[c][1]} nodes)")
