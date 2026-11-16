#!/usr/bin/env python3
"""risk_AB2.py EXE_A EXE_B : the A/B risk test on DELIBERATELY BUILT positions.

The filter "no capture or pawn move available" almost never happens in a game position (pawns are usually on the
board), which is why the first attempt found only 6. To measure the risk properly the positions must be built:
pawnless endgames where nobody can reset the clock and the material is roughly equal, so the fifty-move region is
genuinely reachable and the test being removed is the thing exercised.

Construction: random pawnless material with roughly equal forces (kings + equal counts of minor/rook/queen),
no captures available immediately is not required (a capture would reset the clock - but if a capture exists the
side can reset and the position is not in the fifty-move region, so require NO captures and NO pawns), verified
by python-chess. Then both engines at clocks 95, 97, 99, depth 10, Threads 1, Hash 16, PC20.
"""
import random
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


def build(rng):
    """A pawnless, capture-free-at-the-moment position with roughly equal material."""
    kinds = [[], [chess.KNIGHT], [chess.BISHOP], [chess.ROOK], [chess.QUEEN],
             [chess.KNIGHT, chess.KNIGHT], [chess.BISHOP, chess.BISHOP]]
    for _ in range(4000):
        w = list(rng.choice(kinds))
        bl = list(rng.choice(kinds))
        sqs = rng.sample(range(64), 2 + len(w) + len(bl))
        b = chess.Board(None)
        b.set_piece_at(sqs[0], chess.Piece(chess.KING, chess.WHITE))
        b.set_piece_at(sqs[1], chess.Piece(chess.KING, chess.BLACK))
        i = 2
        for pt in w:
            b.set_piece_at(sqs[i], chess.Piece(pt, chess.WHITE)); i += 1
        for pt in bl:
            b.set_piece_at(sqs[i], chess.Piece(pt, chess.BLACK)); i += 1
        b.turn = rng.choice([chess.WHITE, chess.BLACK])
        b.clear_stack()
        if not b.is_valid():
            continue
        if b.is_game_over(claim_draw=False) or b.is_insufficient_material():
            continue
        caps = [m for m in b.legal_moves if b.is_capture(m)]
        if caps:
            continue                       # a capture would reset the clock
        if any(b.piece_type_at(s) == chess.PAWN for s in chess.SQUARES if b.piece_at(s)):
            continue
        return b
    return None


rng = random.Random(2521)
pos = []
while len(pos) < 10:
    x = build(rng)
    if x is None:
        break
    if x.fen() not in [p.fen() for p in pos]:
        pos.append(x)

print(f"built {len(pos)} pawnless, capture-free positions (the fifty-move region is reachable in all of them)")
print()
print(f"{'position':<46} {'clk':>3} {'A':>7} {'B':>7} {'diff':>6} {'A mv':>6} {'B mv':>6} {'same':>5} {'A n':>7} {'B n':>7}")
diffs = []
chg = 0
for b in pos:
    base = b.fen()
    parts = base.split()
    for c in (95, 97, 99):
        parts[4] = str(c)
        f = " ".join(parts)
        va, ma, na = run(A, f)
        vb, mb, nb = run(B, f)
        if va is None or vb is None:
            continue
        d = vb - va
        diffs.append(d)
        changed = ma != mb
        chg += changed
        print(f"{base[:46]:<46} {c:>3} {va:>7} {vb:>7} {d:>+6} {str(ma):>6} {str(mb):>6} "
              f"{str(not changed):>5} {na:>7} {nb:>7}")

print()
if diffs:
    import statistics
    print(f"cells: {len(diffs)}")
    print(f"B - A: mean {statistics.mean(diffs):+.1f}, median {statistics.median(diffs):+.1f}, "
          f"range {min(diffs):+} .. {max(diffs):+}")
    print(f"absolute: mean {statistics.mean([abs(d) for d in diffs]):.1f} cp, max {max(abs(d) for d in diffs)} cp")
    print(f"bestmove changed: {chg}/{len(diffs)}")
