#!/usr/bin/env python3
"""check_gap_depth.py EXE : does the score gap between best and second-best SHRINK with depth generally?

S-F39 observed, on one board, that the isolated gap between the engine's chosen move and an inferior alternative
SHRANK as depth grew (+231/+239/+198/+100 at depths 12/14/16/18). The coordinator's point: that is checkable
elsewhere, so test it on more boards rather than leaving it as a single observation.

METHOD (clean and comparable across boards):
  for each board and each depth D in 10, 12, 14, 16, 18:
    * MultiPV 2 search at depth D -> the best move B and the second-best move S, with their scores
    * the gap = score(B) - score(S) as REPORTED at that depth
  then ask: does the gap shrink or grow as D rises?
This uses the engine's own two lines at the same depth, so no isolation runs are needed and the comparison is
like-for-like by construction.

Reports per board: the gap at each depth, and the direction (shrink / grow / flat).
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
BOARDS = [
    # the S-F39 board first, as the reference point
    ("S-F39 board", "rnb3nr/3kb2p/1p2p3/p1p2pP1/1PP1p1P1/P3PQ1R/1B1P1P2/RN2KB2 w Q - 0 18"),
    ("G/1 middlegame", "1r6/2k2pp1/2p2n2/2Pppb1p/7P/1P2PPP1/P3BK2/R1R5 b - - 0 1"),
    ("G/2 middlegame", "r3r1k1/p1bb1ppp/1p1q4/3P1p2/1nBP4/PPN2N1P/5PP1/1R1Q1RK1 b - - 0 1"),
    ("G/5 endgame", "8/1p1k1KN1/4pB2/4P2P/8/P2p3r/2b5/8 w - - 0 1"),
    ("G/16 endgame", "8/3n2Q1/2k4p/8/1P6/5P1P/1K4P1/8 b - - 0 1"),
]
DEPTHS = (10, 12, 14, 16, 18)


def multipv2(fen, depth):
    """Returns [(score, move), (score, move)] for the top two lines, from ONE fresh process."""
    p = subprocess.Popen(shlex.split(EXE), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1)

    def until(w):
        for l in p.stdout:
            if l.strip() == w:
                return
    p.stdin.write("uci\n"); p.stdin.flush(); until("uciok")
    p.stdin.write("setoption name Threads value 1\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write("setoption name Hash value 16\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write("setoption name MultiPV value 2\nisready\n"); p.stdin.flush(); until("readyok")
    for n, v in S14 + PC20_EXTRA:
        p.stdin.write(f"setoption name {n} value {v}\n")
    p.stdin.write("isready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write("ucinewgame\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write(f"position fen {fen}\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write(f"go depth {depth}\n"); p.stdin.flush()
    last_by_line = {}
    while True:
        line = p.stdout.readline()
        if not line:
            break
        s = line.rstrip("\n")
        if s.startswith("info depth") and " multipv " in s and " pv " in s:
            m_idx = re.search(r"multipv (\d+)", s)
            m_sc = re.search(r"score (cp|mate) (-?\d+)", s)
            toks = s.split()
            mv = toks[toks.index("pv") + 1] if "pv" in toks and toks.index("pv") + 1 < len(toks) else None
            if m_idx and m_sc and mv:
                val = int(m_sc.group(2))
                if m_sc.group(1) == "mate":
                    val = 30000 - abs(val) if val > 0 else -(30000 - abs(val))
                last_by_line[int(m_idx.group(1))] = (val, mv)
        if s.startswith("bestmove"):
            break
    p.stdin.write("quit\n"); p.stdin.flush()
    try:
        p.wait(timeout=30)
    except subprocess.TimeoutExpired:
        p.kill()
    return last_by_line.get(1), last_by_line.get(2)


print("### does the best-vs-second gap shrink with depth? (MultiPV 2, same depth both lines)")
print(f"exe {EXE} | PC20, Threads 1, Hash 16 | fresh process per search")
print()
verdicts = []
for name, fen in BOARDS:
    print(f"--- {name}")
    print(f"    {fen}")
    gaps = []
    for d in DEPTHS:
        one, two = multipv2(fen, d)
        if one is None or two is None:
            print(f"    depth {d:>2}: only one line available")
            continue
        gap = one[0] - two[0]
        gaps.append((d, gap, one[1], two[1]))
        print(f"    depth {d:>2}: best {one[1]:>5} {one[0]:>7} | second {two[1]:>5} {two[0]:>7} | gap {gap:>5}")
    if len(gaps) >= 3:
        first_gap = gaps[0][1]
        last_gap = gaps[-1][1]
        direction = "SHRINKS" if last_gap < first_gap - 10 else ("GROWS" if last_gap > first_gap + 10 else "FLAT")
        verdicts.append((name, direction, first_gap, last_gap))
        print(f"    -> {direction}: gap {first_gap} at depth {gaps[0][0]} -> {last_gap} at depth {gaps[-1][0]}")
    print()

print("=" * 70)
shr = sum(1 for _, d, _, _ in verdicts if d == "SHRINKS")
gro = sum(1 for _, d, _, _ in verdicts if d == "GROWS")
flat = sum(1 for _, d, _, _ in verdicts if d == "FLAT")
print(f"SHRINKS {shr} | GROWS {gro} | FLAT {flat}  (of {len(verdicts)} boards with >=3 depths)")
for name, d, f, l in verdicts:
    print(f"  {d:<8} {name:<20} {f:>6} -> {l:>5}")
