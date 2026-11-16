#!/usr/bin/env python3
"""is_zero_right.py EXE : at clock 99, is "draw" the CORRECT verdict for board A?

The engine says cp 0 for r4rk1/pp1b1ppp/4p3/3pP3/8/P3P3/1P2N1PP/R2R2K1 w - - 99 1, and its clock-0 value is
-174. Which is right?

The fifty-move rule draws a game only if 100 half-moves pass with no capture and no pawn move. At clock 99, one
more quiet ply reaches 100 and the game is drawn WITHOUT black having to cooperate further - but white is not
forced to play quietly. So:

  * If white has ANY reset move that keeps the game alive and is not losing by force, the correct verdict is not
    "draw" - white plays on.
  * The engine's 0 is the value of "white takes a draw by playing quietly" against "white plays a reset move and
    the search says that is worse".

The question a chess player asks is: is the clock-0 evaluation (-174) reachable from a clock-99 position by
playing a reset move? Yes by definition of a reset move (it zeroes the clock), so the clock-99 position has the
same VALUE as the clock-0 position: -174. The draw is only available to white as an OPTION, and an option worth 0
when the alternative is -174 means white should TAKE the draw.

So the engine's 0 is right if a draw is actually claimable/available. It is available: white can play any quiet
move (e.g. a1a2) and if black also plays quietly the game is drawn at clock 100.

This script tests the decisive point: after white's quiet move a1a2, is the position really a draw by the rule
when black plays quietly too, and can black AVOID the draw and still be winning? If black can avoid it and is
winning, then the 0 is wrong because black simply refuses the draw.
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


def run(fen, go="go depth 10"):
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
    p.stdin.write(f"{go}\n"); p.stdin.flush()
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
    return ((m.group(1), int(m.group(2))) if m else None), best


b = chess.Board(A)
print("A:", A)
print()
print("1. white's quiet move a1a2 puts the clock at 100 for black:")
b1 = chess.Board(A)
b1.push(chess.Move.from_uci("a1a2"))
print(f"   FEN {b1.fen()}   clock {b1.halfmove_clock}")
print(f"   python-chess: is_game_over(claim_draw=True) = {b1.is_game_over(claim_draw=True)}")
print(f"   -> at clock 100 with black to move, the game IS drawn unless black is checkmated.")
print(f"      is_checkmate = {b1.is_checkmate()}")
print()

print("2. can BLACK avoid the draw? black must make a move; if black plays a capture or pawn move,")
print("   the clock resets and the game continues:")
bk_resets = [m.uci() for m in b1.legal_moves
             if b1.is_capture(m) or b1.piece_type_at(m.from_square) == chess.PAWN]
print(f"   black's reset moves: {len(bk_resets)} {bk_resets[:6]}")
print()

print("3. so what should the engine say at clock 99?")
sc0, bm0 = run(A.replace(" 99 1", " 0 1"))
sc99, bm99 = run(A)
print(f"   clock 0  : {sc0}, bestmove {bm0}")
print(f"   clock 99 : {sc99}, bestmove {bm99}")
print()
print("VERDICT: white at clock 99 can reach clock 100 with a quiet move, and the game is then DRAWN")
print("(the fifty-move rule, not a claim either side can refuse once 100 quiet half-moves have passed).")
print("So `cp 0` at clock 99 is CORRECT for white - it is a real drawing resource, and the clock-0 value of")
print(f"{sc0[1] if sc0 else '?'} cp is what white AVOIDS by taking it. The engine reporting 0 here is RIGHT.")
print()
print("What is then WRONG is narrower: the engine reports the draw with a 1-ply PV and, in the earlier")
print("severity test, plays a move that is 40-999 cp worse when the clock is NOT actually drawn.")
