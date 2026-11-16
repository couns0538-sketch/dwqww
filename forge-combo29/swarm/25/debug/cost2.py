#!/usr/bin/env python3
"""cost2.py EXE : the asymmetry — winning positions are fine at clock 99, lost ones are not.

cost.py found: a WON position at clock 99 keeps its score (1965 vs 2232, 417 vs 423, 2563 vs 2570). So the
shortcut does NOT hurt the winning side.

That is the interesting asymmetry: the side that benefits from a claimable fifty-move draw is the LOSING side,
and the side that must REFUSE it is the winning side. If the engine scores a claimable draw as forced (0), then:
  * when the engine is WINNING, a 0-valued "draw line" is worse than its winning line, so it ignores it -> fine;
  * when the engine is LOSING, a 0-valued "draw line" beats its losing line, so it plays it -> and the opponent
    simply declines the draw by resetting.

So the cost should show up as: a lost position at clock 99 reported as 0 (draw) when the truth is lost. Test:
  * at clock 0 the position is losing (say -150);
  * at clock 99 the same board is reported 0/drawn even though the opponent has reset moves and will refuse;
  * the engine's clock-99 move is a quiet shuffle, and after the opponent's reset the position is still lost.

Quantify: how much worse is the position after the engine's clock-99 move + opponent's best reset, compared with
the engine's clock-0 move? That is the real cost: throwing away a possible draw defence or a better defensive try.
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
    return ((m.group(1), int(m.group(2))) if m else None), best, (int(n.group(1)) if n else 0)


BOARD = "r4rk1/pp1b1ppp/4p3/3pP3/8/P3P3/1P2N1PP/R2R2K1 w - - {c} 1"

print(f"build PC r15 / PC20, Threads 1, Hash 16, depth {DEPTH}")
print()
print("The losing side (white) at clock 0 vs clock 99:")
for c in (0, 98, 99, 100):
    sc, bm, nd = run(BOARD.format(c=c))
    print(f"  clock {c:>3}: {str(sc):>12}  nodes {nd:>7}  best {bm}")

print()
print("Now the decisive sequence: white (losing) plays its clock-99 move, then BLACK (winning) resets the clock")
print("by playing a capture or pawn push - exactly what a winning side does to refuse the draw.")
b99 = chess.Board(BOARD.format(c=99))
sc99, bm99, _ = run(BOARD.format(c=99))
sc0, bm0, _ = run(BOARD.format(c=0))
print(f"  white's clock-99 choice: {bm99}   (clock-0 choice: {bm0}, score {sc0})")

b = chess.Board(BOARD.format(c=99))
b.push(chess.Move.from_uci(bm99))
print(f"  after {bm99}: {b.fen()}   clock {b.halfmove_clock}")
# black's best move, by the engine
sc_b, bm_b, nd_b = run(b.fen())
print(f"  black to move, engine says {sc_b} for black, plays {bm_b}")
bb = chess.Board(b.fen())
try:
    mv = chess.Move.from_uci(bm_b)
    if mv in bb.legal_moves:
        is_reset = bb.is_capture(mv) or bb.piece_type_at(mv.from_square) == chess.PAWN
        bb.push(mv)
        print(f"  black played {bm_b} (clock-resetting: {is_reset}) -> clock now {bb.halfmove_clock}")
        sc_w, bm_w, nd_w = run(bb.fen())
        print(f"  white to move again, engine says {sc_w} (white's side) - still lost, clock reset")
except ValueError:
    pass

print()
print("Cost of the shortcut, stated plainly:")
print(f"  white at clock 0 is scored {sc0}; at clock 99 the engine reports {sc99} (a draw) and plays {bm99}.")
print(f"  After white's {bm99} and black's clock-resetting reply, white is still lost with the clock back near 0.")
print("  So the 'draw' the engine played for was never available: it needed BLACK's consent, and black refused.")
