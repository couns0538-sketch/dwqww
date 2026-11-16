#!/usr/bin/env python3
"""check_21F2b.py EXE : 21-F2 done properly — a refused FEN whose side-to-move DIFFERS from the old position.

My first attempt sent a white-to-move refusal after a white-to-move position, so "same answer" could not
distinguish the claim. The claim needs: old position = White to move; refused FEN = Black to move. Then:
  * if the engine keeps the OLD position, the reply must be a WHITE move (the old position's move)
  * if the engine somehow applied the new FEN, the reply would be a BLACK move
Seat 21 says the 2nd answer is Black's move of the old game, i.e. the engine's board has flipped side. I test
directly which side's move comes back, by checking whether each returned move is legal for White or for Black in
the OLD position, and by asking for `go perft 1` (a node count) which is unambiguous.
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
OLD_WHITE = "rnb1kbnr/ppp1pppp/8/4q3/8/2N5/PPPP1PPP/R1BQKBNR w KQkq - 2 4"
REFUSED_BLACK = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBN1 b KQ - 0 1"   # refused, and BLACK to move


def session():
    p = subprocess.Popen(shlex.split(EXE), stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)

    def until(word):
        out = []
        for line in p.stdout:
            out.append(line.rstrip("\n"))
            if line.strip() == word:
                return out
        return out

    def go(cmd):
        p.stdin.write(cmd + "\n"); p.stdin.flush()
        out = []
        while True:
            line = p.stdout.readline()
            if not line:
                break
            s = line.rstrip("\n")
            out.append(s)
            if s.startswith("bestmove"):
                break
            if re.match(r"^nodes \d+", s):
                break
        return out

    p.stdin.write("uci\n"); p.stdin.flush(); until("uciok")
    p.stdin.write("setoption name Threads value 1\nisready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write("setoption name Hash value 16\nisready\n"); p.stdin.flush(); until("readyok")
    for n, v in S14 + PC20:
        p.stdin.write(f"setoption name {n} value {v}\n")
    p.stdin.write("isready\n"); p.stdin.flush(); until("readyok")
    p.stdin.write("ucinewgame\nisready\n"); p.stdin.flush(); until("readyok")

    # 1. the old position, WHITE to move
    p.stdin.write(f"position fen {OLD_WHITE}\n"); p.stdin.flush()
    p.stdin.write("isready\n"); p.stdin.flush(); until("readyok")
    perft_old = go("go perft 1")
    move_old = go("go depth 8")

    # 2. a refused FEN with BLACK to move
    p.stdin.write(f"position fen {REFUSED_BLACK}\n"); p.stdin.flush()
    p.stdin.write("isready\n"); p.stdin.flush()
    ready = until("readyok")
    perft_after = go("go perft 1")
    move_after = go("go depth 8")

    p.stdin.write("quit\n"); p.stdin.flush()
    try:
        p.wait(timeout=10)
    except subprocess.TimeoutExpired:
        p.kill()
    return perft_old, move_old, ready, perft_after, move_after


def nodes_of(lines):
    for l in reversed(lines):
        m = re.search(r"^nodes (\d+)", l)
        if m:
            return int(m.group(1))
        m = re.search(r"info depth \d+.*?nodes (\d+)", l)
        if m:
            return int(m.group(1))
    return None


def bestmove_of(lines):
    for l in reversed(lines):
        if l.startswith("bestmove"):
            return l.split()[-1]
    return None


po, mo, ready, pa, ma = session()
print(f"### 21-F2, done properly — PC r15/PC20, Threads 1, Hash 16")
print()
print(f"OLD position (White to move): {OLD_WHITE}")
print(f"  go perft 1 -> nodes {nodes_of(po)}   go depth 8 -> {bestmove_of(mo)}")
b = chess.Board(OLD_WHITE)
print(f"  python-chess legal moves for White: {b.legal_moves.count()}")
print()
print(f"REFUSED FEN (Black to move, impossible castling): {REFUSED_BLACK}")
print(f"  readyok received: {bool([l for l in ready if l.strip()=='readyok'])}")
print(f"  refusal line: {[l for l in ready if 'invalid' in l.lower()][:1]}")
print(f"  go perft 1 -> nodes {nodes_of(pa)}   go depth 8 -> {bestmove_of(ma)}")
bb = chess.Board(OLD_WHITE)
bb.turn = chess.BLACK
print(f"  python-chess legal moves for BLACK on the old board: {bb.legal_moves.count()}")
print()
n_after = nodes_of(pa)
n_white = b.legal_moves.count()
n_black = bb.legal_moves.count()
print("READING")
print(f"  after the refusal, perft 1 = {n_after}. White has {n_white} legal moves, Black has {n_black}.")
if n_after == n_white:
    print("  -> the engine kept the OLD position with WHITE to move. No wrong-side move.")
elif n_after == n_black:
    print("  -> the side to move FLIPPED to Black: seat 21's wrong-side claim REPRODUCES.")
else:
    print("  -> neither count matches; the board is something else. Report as is.")
