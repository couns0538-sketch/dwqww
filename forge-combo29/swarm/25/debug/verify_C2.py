#!/usr/bin/env python3
"""verify_C2.py EXE FEN : verify one C2 candidate end-to-end.

A C2 candidate: near-balanced at clock 0 (|score| < 100, so drawable), reported cp 0 at clock 99, with a
DIFFERENT bestmove. Verify:
  1. at clock 0 the engine's line is a defensible near-draw;
  2. at clock 99 it reports 0 and plays a different move;
  3. the opponent refuses with a clock-resetting reply;
  4. the original side's score after that refusal is materially worse than its clock-0 score.
If step 4 shows real damage, the shortcut costs a genuinely available drawing/resisting chance.
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
FEN = sys.argv[2]
DEPTH = 10


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
    n = re.search(r"nodes (\d+)", last or "")
    val = None
    if m:
        val = (30000 - abs(int(m.group(2)))) * (1 if int(m.group(2)) > 0 else -1) \
            if m.group(1) == "mate" else int(m.group(2))
    return val, best, (int(n.group(1)) if n else 0), (last or "")


def with_clock(fen, c):
    p = fen.split()
    p[4] = str(c)
    return " ".join(p)


def side_sign(fen):
    """+1 if white to move, -1 if black - so scores can be reported from ONE perspective."""
    return 1 if chess.Board(fen).turn == chess.WHITE else -1


root_sign = side_sign(with_clock(FEN, 0))
print(f"FEN: {FEN}")
print(f"side to move: {'white' if root_sign == 1 else 'black'}  (all scores below from THAT side's view)")
print()

v0, bm0, n0, l0 = run(with_clock(FEN, 0))
v99, bm99, n99, l99 = run(with_clock(FEN, 99))
print(f"clock  0: {v0:>7} cp  nodes {n0:>7}  best {bm0}")
print(f"clock 99: {v99:>7} cp  nodes {n99:>7}  best {bm99}")
print()

b = chess.Board(with_clock(FEN, 99))
mv = chess.Move.from_uci(bm99)
b.push(mv)
print(f"1. play the clock-99 move {bm99} -> clock {b.halfmove_clock}, opponent to move")
v_opp, bm_opp, n_opp, _ = run(b.fen())
print(f"2. opponent's search: {v_opp} cp for the opponent, plays {bm_opp}")
m2 = chess.Move.from_uci(bm_opp)
is_reset = b.is_capture(m2) or b.piece_type_at(m2.from_square) == chess.PAWN
b.push(m2)
print(f"3. opponent played {bm_opp} (clock-resetting: {is_reset}) -> clock {b.halfmove_clock}")
v_after, bm_after, n_after, _ = run(b.fen())
# convert back to the ORIGINAL side's view
after_from_root = -v_after if v_after is not None else None
print(f"4. after the refusal, the original side is scored {after_from_root} cp (at clock 0 it was {v0})")
print()
if v0 is not None and after_from_root is not None:
    delta = v0 - after_from_root
    print(f"COST: {delta:+d} cp worse than the clock-0 continuation, for a 'draw' that was refused.")
    if abs(v0) < 100 and delta > 100:
        print("This is a C2 case: a near-balanced position where the shortcut loses real ground.")
