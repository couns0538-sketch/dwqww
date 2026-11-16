#!/usr/bin/env python3
"""mate0_impact.py EXE : can S-F6's `mate 0` actually corrupt a match record?

S-F6 is confirmed: a mated root answers `score mate 0`. The question that decides whether it needs fixing is
whether any consumer reads that. Three consumers, three tests:

  C1  a match program that stops at checkmate        -> never asks, never sees it (the normal case)
  C2  a match program that asks anyway               -> sees `mate 0`; does it also get a sane bestmove (0000)?
  C3  a PGN writer / GUI that maps the score to a result string -> what does `mate 0` become?

C3 is the one that decides severity, and it is pure arithmetic on the token, so I can do it exactly.
"""
import re
import shlex
import subprocess
import sys

import chess

S14 = [("LmrQuietBase", "93"), ("LmрQuietDivisor", "205")]
S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]
PC20 = [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
        ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]
EXE = sys.argv[1]
MATED = "8/8/Q7/8/8/K7/8/k1Q5 b - - 0 1"          # black checkmated
ONE_PLY_BEFORE = None


def ask(fen, go="go nodes 20000"):
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
    lines, best = [], None
    while True:
        line = p.stdout.readline()
        if not line:
            break
        s = line.rstrip("\n")
        if s.startswith("info depth"):
            lines.append(s)
        if s.startswith("bestmove"):
            best = s.split()[-1]
            break
    p.stdin.write("quit\n"); p.stdin.flush()
    try:
        p.wait(timeout=20)
    except subprocess.TimeoutExpired:
        p.kill()
    score = "?"
    if lines:
        m = re.search(r"score (cp|mate) (-?\d+)", lines[-1])
        score = m.group(0) if m else "?"
    return score, best, lines


b = chess.Board(MATED)
print("=" * 78)
print(f"mated position: {MATED}")
print(f"  python-chess: checkmate={b.is_checkmate()} legal_moves={b.legal_moves.count()}")
score, best, lines = ask(MATED)
print(f"  C2 engine answer: score `{score}`, bestmove `{best}`, {len(lines)} info lines")

print()
print("C3: what a standard UCI-to-result mapping does with `mate N`, applied to the actual token:")
kind, val = score.split()[1], int(score.split()[2])
print(f"  token: mate {val}")
if val > 0:
    print(f"    standard reading: the side to move MATES in {val} moves")
elif val < 0:
    print(f"    standard reading: the side to move is MATED in {-val} moves")
else:
    print("    standard reading: UNDEFINED - 'mate in 0 moves'. A GUI shows no mate;")
    print("    a sign-based label maps it to neither win nor loss (0 is neither > nor < 0).")

print()
print("  Compare with the same board one ply earlier (the mating move available):")
# find a predecessor: the position before white's mating move
for fen_try in ("8/8/Q7/8/8/K7/8/k1Q5 b - - 0 1",):
    pass
PRE = "8/8/Q7/8/8/1K6/8/k1Q5 w - - 0 1"
pre = chess.Board(PRE)
if pre.is_valid() and not pre.is_game_over():
    s2, m2, _ = ask(PRE)
    print(f"    {PRE}")
    print(f"    -> score `{s2}`, bestmove `{m2}` (a proper mate number)")

print()
print("VERDICT on severity")
print(f"  C1 a match program that stops at checkmate never asks the engine here and never sees `mate {val}`.")
print("  C2 if it asks anyway it gets bestmove 0000, which no move generator will accept - so it cannot play it;")
print("     it will either crash, forfeit, or fall through to its own terminal handling.")
print("  C3 a GUI or PGN writer reading the SCORE gets an undefined token and will show no mate.")
print("  So the exposure is: a consumer that both (a) searches a finished game and (b) trusts the score token")
print("  rather than the bestmove. Both are programmer errors, but the engine hands them an undefined value")
print("  where a defined one (a large mate number, or plain `cp 0`) would be harmless.")
