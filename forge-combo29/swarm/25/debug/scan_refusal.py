#!/usr/bin/env python3
"""scan_refusal.py EXE FENS N : for every clock-99-affected position found, does the OPPONENT actually refuse?

The earlier scan (find_lost_draw.py) classified positions by score alone. That is not enough to establish a cost:
a "draw" is only wrongly awarded if the opponent will actually REFUSE it, i.e. the opponent's own best reply is a
clock-RESETTING move (capture or pawn push) while the side that just shuffled wanted the draw.

For each affected position this script:
  1. confirms clock-0 vs clock-99 divergence;
  2. plays the clock-99 move;
  3. asks the engine (as the opponent) for its reply;
  4. records whether that reply RESETS the clock, and what the original side's score becomes afterwards.
Only rows where the reply resets the clock count as "the draw was refused". Those are the real-cost rows.
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
CANDIDATES = [l.strip() for l in open(sys.argv[2]) if l.strip() and not l.startswith("#")]
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
    val = None
    if m:
        val = (30000 - abs(int(m.group(2)))) * (1 if int(m.group(2)) > 0 else -1) \
            if m.group(1) == "mate" else int(m.group(2))
    return val, best


def wc(fen, c):
    p = fen.split()
    p[4] = str(c)
    return " ".join(p)


print(f"{'position':<50} {'c0':>7} {'c99':>6} {'shuffle':>8} {'reply':>7} {'reset':>6} {'then':>7}  verdict")
refused = []
for fen in CANDIDATES:
    b0 = chess.Board(wc(fen, 0))
    if b0.is_game_over(claim_draw=False):
        continue
    sign = 1 if b0.turn == chess.WHITE else -1
    v0, bm0 = run(wc(fen, 0))
    v99, bm99 = run(wc(fen, 99))
    if v99 != 0 or v0 is None or v0 == 0:
        continue
    b = chess.Board(wc(fen, 99))
    try:
        m1 = chess.Move.from_uci(bm99)
    except (ValueError, TypeError):
        continue
    if m1 not in b.legal_moves:
        continue
    b.push(m1)
    v_opp, bm_opp = run(b.fen())
    if not bm_opp:
        continue
    try:
        m2 = chess.Move.from_uci(bm_opp)
    except ValueError:
        continue
    if m2 not in b.legal_moves:
        continue
    is_reset = b.is_capture(m2) or b.piece_type_at(m2.from_square) == chess.PAWN
    b.push(m2)
    v_after, _ = run(b.fen())
    after = -v_after * 1 if v_after is not None else None
    verdict = "REFUSED (real cost)" if is_reset else "draw still available"
    if is_reset:
        refused.append((fen, v0, bm99, bm_opp, after, sign))
    print(f"{fen[:50]:<50} {v0:>7} {v99:>6} {str(bm99):>8} {str(bm_opp):>7} "
          f"{str(is_reset):>6} {str(after):>7}  {verdict}")

print()
print(f"positions where the opponent REFUSES the draw with a clock reset: {len(refused)}")
for fen, v0, bm99, bm_opp, after, sign in refused[:10]:
    print(f"  {fen}  c0={v0} shuffle={bm99} refused_by={bm_opp} then={after}")
