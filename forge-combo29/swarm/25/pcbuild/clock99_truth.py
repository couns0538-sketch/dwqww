#!/usr/bin/env python3
"""clock99_truth.py EXE : what SHOULD the engine answer at clock 99, and how wrong is cp 0?

At clock 99 with 9 legal clock-resetting moves, the position is not a draw: any capture or pawn move resets
the counter and the game continues. To price the error, take the engine's OWN clock-0 evaluation of the
position (the same board with clock 0, which is not a draw and which the engine searches fully) and compare
it with the cp 0 it reports at clock 99.

Also check: does the engine, at clock 99, at least PLAY a resetting move if forced to? No - it plays a1a2.
And: what does it do at clock 99 when a capture is the ONLY legal move? (Then cp 0 would be doubly wrong.)
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
PC20_EXTRA = [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
              ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]
EXE = sys.argv[1]


def run(fen, depth=12):
    p = subprocess.Popen(shlex.split(EXE), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)

    def until(w):
        for l in p.stdout:
            if l.strip() == w:
                return
    p.stdin.write("uci\n"); p.stdin.flush(); until("uciok")
    p.stdin.write("setoption name Threads value 1\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write("setoption name Hash value 16\nisready\n"); p.stdin.flush(); until("readyok")
    for n, v in S14 + PC20_EXTRA:
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


BASE = "r4rk1/pp1b1ppp/4p3/3pP3/8/P3P3/1P2N1PP/R2R2K1 w - - {c} 1"
print("Q1: how far is `cp 0` from the engine's own evaluation of the same board at clock 0?")
sc0, bm0, n0 = run(BASE.format(c=0))
sc99, bm99, n99 = run(BASE.format(c=99))
print(f"  clock 0 : {sc0} in {n0} nodes, best {bm0}")
print(f"  clock 99: {sc99} in {n99} nodes, best {bm99}")
if sc0 and sc99 and sc0[0] == "cp":
    print(f"  -> the engine calls a {sc0[1]:+d} cp position `cp 0` at clock 99: an error of {abs(sc0[1])} cp")
print()

print("Q2: with a capture the ONLY legal move, is it still cp 0?")
# force a position where every legal move is a capture, at clock 99
made = None
for fen_try in [
    "4k3/8/8/8/8/8/4r3/4K3 w - - 99 1",      # Ke1 attacked only by rook on e2: Kxe2 is the only capture-ish
    "8/8/8/8/8/2k5/1q6/1K6 w - - 99 1",      # Kxb2 only legal move
]:
    b = chess.Board(fen_try)
    legal = list(b.legal_moves)
    caps = [m for m in legal if b.is_capture(m)]
    print(f"  try {fen_try}")
    print(f"     legal {len(legal)}, of which captures {len(caps)}: {[m.uci() for m in legal][:4]}")
    if legal and len(caps) == len(legal):
        made = fen_try
        break
if made:
    sc, bm, nd = run(made, depth=10)
    print(f"  forced-capture position at clock 99 -> {sc} in {nd} nodes, best {bm}")
    print("  (a capture RESETS the counter, so the game cannot be drawn here; cp 0 would be wrong)")
else:
    print("  did not construct an all-capture position; not claimed")
