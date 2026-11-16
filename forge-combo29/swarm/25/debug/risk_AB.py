#!/usr/bin/env python3
"""risk_AB.py EXE_A EXE_B : the risk of removing the fifty-move test, measured not argued.

EXE_A = PC r15 build with the fifty-move test present (normal)
EXE_B = the same source with the test removed from is_draw (FORGE_CLOCK99_NORULE50)

Positions required by the coordinator: ten at halfmove clock 95..99 where
  * the clock-0 score is nearly equal (|score| <= 100, so the position is close to a draw anyway), and
  * NO clock-resetting move is available to either side on the board now (so the fifty-move region really is
    reachable and the test is the thing being exercised).

For each position, both engines at depth 10, Threads 1, Hash 16, PC20, and report:
  A score / B score / difference, A move / B move, and node counts.
A small, bounded difference means the fix is safe; a large one is what the owner must see before choosing.
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
        p.wait(timeout=10)
    except subprocess.TimeoutExpired:
        p.kill()
    m = re.search(r"score (cp|mate) (-?\d+)", last or "")
    val = None
    if m:
        val = (30000 - abs(int(m.group(2)))) * (1 if int(m.group(2)) > 0 else -1) \
            if m.group(1) == "mate" else int(m.group(2))
    n = re.search(r"nodes (\d+)", last or "")
    return val, best, (int(n.group(1)) if n else 0)


def wc(fen, c):
    p = fen.split()
    p[4] = str(c)
    return " ".join(p)


def resets(fen):
    b = chess.Board(fen)
    return [m.uci() for m in b.legal_moves
            if b.is_capture(m) or b.piece_type_at(m.from_square) == chess.PAWN]


# Candidate pool: positions from G whose clock-0 score is near equal and which have NO resetting move.
fens = []
for path in ("/agent/repos/dwqww/forge-combo29/swarm/25/positions/set_G.epd",
             "/agent/repos/dwqww/forge-combo29/swarm/25/job1b/R2_2511.fens"):
    fens += [l.split(";")[0].strip() for l in open(path) if l.strip()]

picked = []
print("selecting ten positions: |score at clock 0| <= 100 and NO clock-resetting move available")
print(f"{'fen':<50} {'c0':>6} {'resets':>6}")
for fen in fens:
    if len(picked) >= 10:
        break
    b = chess.Board(wc(fen, 0))
    if b.is_game_over(claim_draw=False):
        continue
    if resets(wc(fen, 0)):
        continue                       # need no reset available
    v0, bm0, _ = run(A, wc(fen, 0))
    if v0 is None or abs(v0) > 100:
        continue
    picked.append((fen, v0))
    print(f"{fen[:50]:<50} {v0:>6} {0:>6}")

if len(picked) < 10:
    print(f"\nWARNING: only {len(picked)} positions met the strict filter")

print()
print("=" * 96)
print("A = fifty-move test PRESENT (normal build)   B = test REMOVED from is_draw")
print(f"{'position':<42} {'clk':>3} {'A score':>8} {'B score':>8} {'diff':>6} {'A move':>6} {'B move':>6} {'same?':>5}")
diffs = []
moves_differ = 0
for fen, v0 in picked:
    for c in (95, 97, 99):
        f = wc(fen, c)
        va, ma, na = run(A, f)
        vb, mb, nb = run(B, f)
        if va is None or vb is None:
            continue
        d = vb - va
        diffs.append(d)
        same = ma == mb
        moves_differ += (not same)
        print(f"{fen[:42]:<42} {c:>3} {va:>8} {vb:>8} {d:>+6} {str(ma):>6} {str(mb):>6} {str(same):>5}")

print()
if diffs:
    import statistics
    print(f"cells compared: {len(diffs)}")
    print(f"score difference (B - A): mean {statistics.mean(diffs):+.1f} cp, "
          f"median {statistics.median(diffs):+.1f}, min {min(diffs):+}, max {max(diffs):+}")
    print(f"absolute difference: mean {statistics.mean([abs(d) for d in diffs]):.1f} cp, "
          f"max {max(abs(d) for d in diffs)}")
    print(f"cells whose bestmove changed: {moves_differ}/{len(diffs)}")
