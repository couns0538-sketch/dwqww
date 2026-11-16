#!/usr/bin/env python3
"""find_lost_draw.py EXE : find a position where the clock-99 shortcut throws away a REAL drawing resource.

What "real" means here, precisely: at clock 0 the engine's best move holds or improves the score (the position is
drawable), while at clock 99 the engine reports 0 and plays a quiet shuffle, and after the opponent's clock-resetting
reply the engine's own score for the original side is WORSE than the clock-0 score by a lot.

Two classes are worth separating:
  C1 (what I expect to find): a LOST position reported as 0 - the engine pretends to draw, the opponent refuses,
     the side ends up worse than its own clock-0 defence. Already shown on one board (S-F18).
  C2 (what would matter most): a position where the clock-0 line really DRAWS (score ~0 by holding) but the
     clock-99 shuffle loses. For this the clock-0 score would have to be about 0 and the clock-99 move would have
     to be clearly worse after the refusal - but the clock-99 score is ALSO 0, so the engine cannot tell them
     apart. C2 requires a board where the true value with best play is 0 and the shuffle loses.

Method: sample middlegame positions from set G, run each at clock 0 and at clock 99, and keep the cases where
  |score(clock 0)| < 100 (drawable) and clock 99 reports 0 and bestmoves differ,
then verify the clock-99 move by playing it and having the engine reply.
"""
import json
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
FENS = sys.argv[2]
LIMIT = int(sys.argv[3]) if len(sys.argv) > 3 else 60
DEPTH = 8


def run(fen, depth=DEPTH):
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
    val = None
    if m:
        val = (30000 - abs(int(m.group(2)))) * (1 if int(m.group(2)) > 0 else -1) \
            if m.group(1) == "mate" else int(m.group(2))
    return val, best


def with_clock(fen, c):
    parts = fen.split()
    parts[4] = str(c)
    return " ".join(parts)


fens = [l.split(";")[0].strip() for l in open(FENS) if l.strip()][:LIMIT]
print(f"scanning {len(fens)} positions at depth {DEPTH}, clock 0 vs clock 99")
print(f"{'fen':<56} {'c0':>7} {'c99':>7} {'bm0':>6} {'bm99':>6}  note")
candidates = []
for fen in fens:
    b = chess.Board(with_clock(fen, 0))
    if b.is_game_over(claim_draw=False):
        continue
    v0, bm0 = run(with_clock(fen, 0))
    v99, bm99 = run(with_clock(fen, 99))
    if v0 is None or v99 is None:
        continue
    note = ""
    if v99 == 0 and abs(v0) < 100:
        note = "C2-candidate: drawable at clock 0, reported 0 at 99"
        candidates.append((fen, v0, v99, bm0, bm99, "C2"))
    elif v99 == 0 and v0 < -100:
        note = "C1: lost at clock 0, reported 0 at 99"
        candidates.append((fen, v0, v99, bm0, bm99, "C1"))
    if note:
        print(f"{fen:<56} {v0:>7} {v99:>7} {str(bm0):>6} {str(bm99):>6}  {note}")

print()
print(f"candidates: {len(candidates)}  (C2 = drawable-then-shuffled, C1 = lost-then-labelled-draw)")
for fen, v0, v99, bm0, bm99, cls in candidates:
    print(f"  {cls} {fen}  c0={v0} c99={v99} bm0={bm0} bm99={bm99}")
    if cls == "C1" and len(candidates) <= 3:
        # verify the refusal
        b = chess.Board(with_clock(fen, 99))
        try:
            mv = chess.Move.from_uci(bm99)
        except ValueError:
            continue
        if mv not in b.legal_moves:
            continue
        b.push(mv)
        v_opp, bm_opp = run(b.fen())
        if v_opp is not None and bm_opp:
            try:
                m2 = chess.Move.from_uci(bm_opp)
                if m2 in b.legal_moves:
                    is_reset = b.is_capture(m2) or b.piece_type_at(m2.from_square) == chess.PAWN
                    b.push(m2)
                    v_after, _ = run(b.fen())
                    print(f"      after {bm99}, opponent plays {bm_opp} (reset={is_reset}) -> original side now "
                          f"{v_after} vs clock-0 {v0}")
            except ValueError:
                pass
