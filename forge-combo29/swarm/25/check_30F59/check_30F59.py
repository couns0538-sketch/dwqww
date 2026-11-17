#!/usr/bin/env python3
"""check_30F59.py EXE : does PC20 really pick a 200+ cp inferior move at depths 10-16 here?

SEAT 30's 30-F59, which I am checking:
  On `rnb3nr/3kb2p/1p2p3/p1p2pP1/1PP1p1P1/P3PQ1R/1B1P1P2/RN2KB2 w Q - 0 18`, unrestricted PC20 gives `f3g3`
  (cp 1627/1724/1824 at depths 12/14/16), while `f3g2` - which PC20 itself scores 190-230 cp higher in isolation -
  is only chosen at depth 18 (cp 2088). S14 chooses `f3g2` at every depth. So the four PC20 search switches cost a
  real move at self-play depths on at least this position.

WHY IT MATTERS: PC20 is what the owner's matches use, and self-play runs at depth ~7-8. If PC20's switches make it
choose a materially worse move at low depth, that is a real cost of the PC's own configuration - in my area (scores
and move choice).

MY CHECK, independent harness:
  * unrestricted search at depths 10, 12, 14, 16, 18, 20 under PC20 and under S14: which move, and its score
  * the two candidate moves scored IN ISOLATION at the same depths, so the comparison is like-for-like
  * a fresh process per search
If PC20 picks f3g3 at 10-16 and f3g2 at 18-20 while S14 picks f3g2 throughout, the claim holds.
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
FEN = "rnb3nr/3kb2p/1p2p3/p1p2pP1/1PP1p1P1/P3PQ1R/1B1P1P2/RN2KB2 w Q - 0 18"


def run(fen, depth, pc20, restrict=None):
    p = subprocess.Popen(shlex.split(EXE), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1)

    def until(w):
        for l in p.stdout:
            if l.strip() == w:
                return
    p.stdin.write("uci\n"); p.stdin.flush(); until("uciok")
    p.stdin.write("setoption name Threads value 1\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write("setoption name Hash value 16\nisready\n"); p.stdin.flush(); until("readyok")
    opts = S14 + (PC20_EXTRA if pc20 else [])
    for n, v in opts:
        p.stdin.write(f"setoption name {n} value {v}\n")
    p.stdin.write("isready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write("ucinewgame\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write(f"position fen {fen}\nisready\n"); p.stdin.flush(); until("readyok")
    go = f"go depth {depth}"
    if restrict:
        go += f" searchmoves {restrict}"
    p.stdin.write(f"{go}\n"); p.stdin.flush()
    last, best = None, None
    while True:
        line = p.stdout.readline()
        if not line:
            break
        s = line.rstrip("\n")
        if s.startswith("info depth"):
            last = s
        if s.startswith("bestmove"):
            best = s.split()[-1]
            break
    p.stdin.write("quit\n"); p.stdin.flush()
    try:
        p.wait(timeout=30)
    except subprocess.TimeoutExpired:
        p.kill()
    m = re.search(r"score (cp|mate) (-?\d+)", last or "")
    return (m.group(0) if m else "?"), best


print("### 30-F59 check: does PC20 choose a worse move at low depth here?")
print(f"fen {FEN}")
print(f"fresh process per search, Threads 1, Hash 16")
print()
print(f"{'depth':>6} | {'PC20 unrestricted':>22} | {'S14 unrestricted':>22} |  PC20 move better/worse?")
for d in (10, 12, 14, 16, 18, 20):
    s_pc, m_pc = run(FEN, d, True)
    s_s14, m_s14 = run(FEN, d, False)
    print(f"{d:>6} | {s_pc:>12} {str(m_pc):>8} | {s_s14:>12} {str(m_s14):>8} |")

print()
print("Isolated scores of the two candidate moves, so the comparison is like-for-like at each depth:")
print(f"{'depth':>6} | {'PC20 f3g3':>12} {'PC20 f3g2':>12} {'gap (g2-g3)':>12} | {'S14 f3g3':>11} {'S14 f3g2':>11}")
for d in (12, 14, 16, 18):
    pc_g3, _ = run(FEN, d, True, "f3g3")
    pc_g2, _ = run(FEN, d, True, "f3g2")
    s_g3, _ = run(FEN, d, False, "f3g3")
    s_g2, _ = run(FEN, d, False, "f3g2")

    def num(s):
        m = re.search(r"(-?\d+)", s or "")
        return int(m.group(1)) if m else 0
    print(f"{d:>6} | {pc_g3:>12} {pc_g2:>12} {num(pc_g2) - num(pc_g3):>+12} | {s_g3:>11} {s_g2:>11}")
