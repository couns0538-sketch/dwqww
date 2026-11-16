#!/usr/bin/env python3
"""risk_diagnose.py : is the A/B gap a REAL repair risk, or just A being right about dead draws?

risk_AB2 showed: removing the fifty-move test changes scores by mean |323| cp (max 1230) and 21/30 bestmoves.
That number alone would say "the fix is dangerous". But look at the positions: several are DEAD DRAWS that the
engine grounds to 0 correctly (K+N vs K+N with a lone knight each, K+R vs K, K+B+N vs K+N...). For those, A = 0 is
RIGHT and B = some number is the variant being WRONG - not the other way round. The gap then measures "B overvalues
dead draws", which is exactly the risk I predicted, but it should be stated with the right sign and the right cases.

This script splits the 30 cells into:
  G1  positions where A = 0 and the position is genuinely dead drawn (python-chess: insufficient material, or a
      bare-king / lone-minor ending) -> B's deviation is B's error
  G2  positions where A = 0 and the position is NOT dead drawn (a real result exists) -> B's number may be B's
      correction of A's bug, or B's error; these are the interesting rows
  G3  positions where A != 0 -> neither engine is being fooled by the dead-draw path

and reports the gap per group plus node costs (B searches the fifty-move region, so it should cost far more).
"""
import re
import shlex
import subprocess
import sys

import chess

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]
PC20 = [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
        ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]
A, B = sys.argv[1], sys.argv[2]
DEPTH = 10

POSITIONS = [
    "k7/8/8/8/8/8/1B5n/1K6 b - - 0 1",
    "6N1/8/3N4/4n3/8/1k6/8/4K3 b - - 0 1",
    "8/6K1/2b5/7N/2k2N2/8/8/8 w - - 0 1",
    "8/8/6r1/1K6/8/6N1/8/1k6 w - - 0 1",
    "8/8/8/R5K1/8/8/4k3/8 w - - 0 1",
    "8/8/1n6/4K3/8/8/n7/6k1 w - - 0 1",
    "4k3/8/8/8/8/1K6/1N6/7q w - - 0 1",
    "4n2B/8/8/4Bk2/8/2K5/8/6n1 b - - 0 1",
    "1k6/8/7K/8/8/6r1/8/8 w - - 0 1",
    "6K1/8/8/k1q5/8/8/8/8 w - - 0 1",
]


def run(exe, fen, depth=DEPTH):
    p = subprocess.Popen(shlex.split(exe), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
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
        p.wait(timeout=20)
    except subprocess.TimeoutExpired:
        p.kill()
    m = re.search(r"score (cp|mate) (-?\d+)", last or "")
    val = None
    if m:
        val = (30000 - abs(int(m.group(2)))) * (1 if int(m.group(2)) > 0 else -1) \
            if m.group(1) == "mate" else int(m.group(2))
    n = re.search(r"nodes (\d+)", last or "")
    return val, best, (int(n.group(1)) if n else 0)


def material(b):
    counts = {}
    for sq in chess.SQUARES:
        pc = b.piece_at(sq)
        if pc and pc.piece_type != chess.KING:
            key = (pc.color, pc.piece_type)
            counts[key] = counts.get(key, 0) + 1
    return counts


def is_dead_drawn(b):
    """A conservative test: python-chess's insufficient material, or at most one minor piece per side."""
    if b.is_insufficient_material():
        return True
    m = material(b)
    non_kings = sum(m.values())
    minors = sum(v for (c, t), v in m.items() if t in (chess.KNIGHT, chess.BISHOP))
    # one minor (or none) on each side, nothing else
    return non_kings <= 2 and minors == non_kings


print(f"{'position':<44} {'clk':>3} {'A':>7} {'B':>7} {'gap':>6} {'Anodes':>7} {'Bnodes':>7} {'grp':>4}  dead-drawn?")
groups = {"G1": [], "G2": [], "G3": []}
node_ratio = []
for base in POSITIONS:
    parts = base.split()
    b = chess.Board(base)
    dead = is_dead_drawn(b)
    for c in (95, 97, 99):
        parts[4] = str(c)
        f = " ".join(parts)
        va, ma, na = run(A, f)
        vb, mb, nb = run(B, f)
        if va is None or vb is None:
            continue
        gap = vb - va
        grp = "G3"
        if va == 0:
            grp = "G1" if dead else "G2"
        groups[grp].append(gap)
        if na > 0:
            node_ratio.append(nb / na)
        print(f"{base[:44]:<44} {c:>3} {va:>7} {vb:>7} {gap:>+6} {na:>7} {nb:>7} {grp:>4}  {dead}")

import statistics
print()
for g in ("G1", "G2", "G3"):
    v = groups[g]
    if not v:
        print(f"{g}: no cells")
        continue
    print(f"{g}: {len(v)} cells | gap mean {statistics.mean(v):+.1f} | mean |gap| "
          f"{statistics.mean([abs(x) for x in v]):.1f} | max |gap| {max(abs(x) for x in v)}")
print()
if node_ratio:
    print(f"node cost of B vs A: median ratio {statistics.median(node_ratio):.1f}x, "
          f"max {max(node_ratio):.1f}x")
print()
print("Reading:")
print("  G1 = A says 0 AND the position is dead drawn: A is RIGHT, B's number is B overvaluing a dead draw.")
print("  G2 = A says 0 but a real result exists: B may be correcting A's bug, or B may be wrong; worth inspecting.")
print("  G3 = A was not fooled; the gap there is ordinary search difference.")
