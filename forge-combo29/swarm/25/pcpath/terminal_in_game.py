#!/usr/bin/env python3
"""terminal_in_game.py EXE : do S-F6/S-F7 ever fire in a REAL game that ends in mate?

My 90-ply self-play game ended by threefold repetition, so S-F6 (`score mate 0` on a checkmated root) and S-F7
(64 phantom info lines on a terminal root) were never exercised. They only matter if a match can actually ask the
engine to search a terminal position — i.e. if a match program calls `go` on a position that is already mate or
stalemate. A well-written match program stops first; a naive one does not.

Test: play a forced mate sequence to completion with python-chess, then at the FINAL (mated) position ask the
engine `go nodes 20000` exactly as a naive match program would, and record:
  * the score token (does `mate 0` appear?)
  * how many info lines come back (64 = S-F7 fires)
  * the bestmove (0000 expected)
Control: the position one ply EARLIER must search normally, otherwise the test is not measuring a terminal root.
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


def ask(fen, go):
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
    return len(lines), best, score, lines


# A forced mate: white mates in 2 with Ra8+ then another, from a simple KRK-like setting with the queen
# Simple forced mate: 6k1/5ppp/8/8/8/8/5PPP/R5K1 w -> Ra8# is mate in 1. Use a mate-in-2 instead so the
# one-ply-earlier control is a real search.
MATE_IN_2 = "7k/8/6K1/8/8/8/8/R7 w - - 0 1"     # Ra8# is mate in 1 actually; use it as the mate-in-1


def find_mate_line(start_fen, plies):
    """Play the shortest forced mate with python-chess's own search (brute force at small depth)."""
    b = chess.Board(start_fen)
    path = []
    for _ in range(plies):
        # pick any move that leads to mate in the remaining plies, else the first legal
        chosen = None
        for mv in b.legal_moves:
            b.push(mv)
            if b.is_checkmate() and plies - len(path) == 1:
                chosen = mv
                b.pop()
                break
            b.pop()
        if chosen is None:
            chosen = next(iter(b.legal_moves))
        b.push(chosen)
        path.append(chosen.uci())
        if b.is_checkmate():
            break
    return path, b


for name, start in (("mate in 1 (Ra8#)", "6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 0 1"),):
    path, bfinal = find_mate_line(start, 1)
    bmid = chess.Board(start)
    print("=" * 78)
    print(f"{name}: {start}")
    print(f"  mating line: {path}  -> final checkmate={bfinal.is_checkmate()}")
    # control: the position before the mating move
    n, best, score, _ = ask(start, "go nodes 20000")
    print(f"  CONTROL (before the mate): info lines {n}, bestmove {best}, score {score}")
    # terminal root
    n, best, score, lines = ask(bfinal.fen(), "go nodes 20000")
    print(f"  TERMINAL ROOT (after the mate): info lines {n}, bestmove {best}, score {score}")
    if lines:
        print(f"    first: {lines[0][:96]}")
        print(f"    last : {lines[-1][:96]}")
    print()
    print(f"  S-F6 fires (mate 0 on a checkmated root)? {'YES' if 'mate 0' in score else 'no'}")
    print(f"  S-F7 fires (>=60 phantom info lines)?     {'YES' if n >= 60 else 'no'}  (lines={n})")
