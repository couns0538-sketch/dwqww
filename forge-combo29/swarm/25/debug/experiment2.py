#!/usr/bin/env python3
"""experiment2.py EXE : the score-0-at-every-depth + pv_len-1 signature.

Experiment 1 ruled out the root shortcut paths (root_drawn=0, no EMERGENCY line, no ROOT-SHORTCUT line).
It showed instead:
  A (breaking, clock 99): ROOT ITER SEARCHED depth 1..6, score 0 at EVERY depth, pv_len stays 1
  B (fine,    clock 99): score 462/501/485/466/531/511, pv_len grows 1..7
  C (control, clock 98): normal, score varies

So the search DOES run on A, and returns exactly 0 with a 1-move PV. A one-move PV with score 0 means the
root's best move leads to a position evaluated as 0 — and every child of A is at clock 100 (the is_draw
lines show clock=100 children), where `is_draw` returns TRUE for a non-mate position.

The discriminating question: at clock 99, does the engine consider the children draws? It should NOT — a
child at clock 100 is a draw only if the move played into it did not reset the clock, which is true for quiet
moves, so the fifty-move rule DOES apply to those children. That is CORRECT for quiet lines.

The real defect then is not "0 at clock 99" but "0 EVERYWHERE at clock 99 with a 1-ply PV", i.e. the engine
reports a draw without checking whether a clock-RESETTING move exists. Test: at clock 99, is there a capture
or pawn move that leads to a NON-draw position, and does the engine consider it?

This script enumerates A's reset moves, plays each, and searches the resulting position at clock 0 (so no
fifty-move interference) to see whether the side to move escapes the draw.
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
EXE = sys.argv[1]
A = "r4rk1/pp1b1ppp/4p3/3pP3/8/P3P3/1P2N1PP/R2R2K1 w - - 99 1"


def run(fen, depth=8):
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
    n = re.search(r"nodes (\d+)", last or "")
    return ((m.group(1), int(m.group(2))) if m else None), best, (int(n.group(1)) if n else 0)


b = chess.Board(A)
print("A at clock 99:", A)
print(f"legal moves {b.legal_moves.count()}, halfmove clock {b.halfmove_clock}")
print()
print("The engine's own answer:", run(A))

print()
print("Every RESET move (capture or pawn push), then the resulting position searched at clock 0:")
print("(if a reset move leads to a non-zero score, the clock-99 answer of 0 is wrong for the side to move)")
rows = []
for m in b.legal_moves:
    is_reset = b.is_capture(m) or b.piece_type_at(m.from_square) == chess.PAWN
    if not is_reset:
        continue
    b.push(m)
    fen_after = b.fen()
    # search with the clock zeroed, so the fifty-move rule cannot interfere
    parts = fen_after.split()
    parts[4] = "0"
    fen_zero = " ".join(parts)
    sc, bm, nd = run(fen_zero, depth=8)
    print(f"  {m.uci():<6} {'capture' if b.is_capture(m) else 'pawn-push'} -> after-move clock {b.halfmove_clock:>2}, "
          f"searched at clock 0: {str(sc):>12} nodes {nd:>6} best {bm}")
    rows.append((m.uci(), sc))
    b.pop()

print()
nz = [r for r in rows if r[1] and r[1][1] != 0]
print(f"reset moves found: {len(rows)}; of those, non-zero score after the reset: {len(nz)}")
for u, sc in nz:
    print(f"  {u} -> {sc}")
print()
if nz:
    print("VERDICT: the position at clock 99 is NOT a draw — at least one legal resetting move keeps the game")
    print("         alive with a non-zero evaluation, yet the engine reports cp 0 and a 1-ply PV.")
else:
    print("VERDICT: every reset move still leads to 0, so the clock-99 0 may be a genuine draw.")
