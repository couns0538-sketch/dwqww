#!/usr/bin/env python3
"""filter_blindspot.py EXE : does the PV-length filter have a blind spot I can demonstrate?

I just stated the filter's limit: it catches every observed failure but does NOT validate a passing score, because a
right-length PV ending in checkmate could still be a longer mate than necessary.

That is a claim about a blind spot. Can I DEMONSTRATE one? Test: for each board, search at a small budget and at a
large one. If the small budget reports `mate N` with a right-length PV that IS checkmate, but the large budget
reports `mate M` with M < N, then the small-budget score PASSED my filter while being wrong about the distance -
a concrete demonstration of the blind spot.

This is the difference between "my filter might have a blind spot" (a caveat) and "here is one" (a finding).
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
BOARDS = ["4Q3/8/r2K4/8/2B5/5R2/1k6/8 w - - 0 1",
          "7Q/8/8/4K3/8/8/5k2/4R3 w - - 0 1",
          "8/8/4R3/8/7Q/8/1k4K1/8 w - - 0 1",
          "K7/7Q/8/8/4R3/8/5k2/8 w - - 0 1",
          "6Q1/2K5/8/R7/8/8/8/3k4 w - - 0 1"]


def run(fen, go):
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
    last = None
    while True:
        line = p.stdout.readline()
        if not line:
            break
        s = line.rstrip("\n")
        if s.startswith("info depth") and " pv" in s:
            last = s
        if s.startswith("bestmove"):
            break
    p.stdin.write("quit\n"); p.stdin.flush()
    try:
        p.wait(timeout=30)
    except subprocess.TimeoutExpired:
        p.kill()
    if last is None:
        return None, []
    m = re.search(r"score mate (-?\d+)", last)
    toks = last.split()
    pv = toks[toks.index("pv") + 1:] if "pv" in toks else []
    return (int(m.group(1)) if m else None), pv


def passes_filter(fen, mate, pv):
    """True if the PV is right-length AND ends in checkmate (the filter's accept condition)."""
    b = chess.Board(fen)
    for mv in pv:
        try:
            mm = chess.Move.from_uci(mv)
        except ValueError:
            return False
        if mm not in b.legal_moves:
            return False
        b.push(mm)
    need = 2 * mate - 1 if mate > 0 else 2 * abs(mate)
    return b.is_checkmate() and len(pv) == need


print("### can I DEMONSTRATE the filter's blind spot? (a passing score that is still a longer mate)")
print(f"{'board':<40} {'small budget':>22} {'large budget':>18}  blind spot?")
found = []
for fen in BOARDS:
    small = run(fen, "go softnodes 1000")
    large = run(fen, "go softnodes 100000")
    if small[0] is None or large[0] is None:
        print(f"{fen[:40]:<40} {'no mate':>22} {str(large[0]):>18}")
        continue
    sp = passes_filter(fen, *small)
    lp = passes_filter(fen, *large)
    blind = sp and large[0] < small[0]
    if blind:
        found.append((fen, small[0], large[0]))
    print(f"{fen[:40]:<40} {('mate ' + str(small[0]) + (' PASS' if sp else ' fail')):>22} "
          f"{('mate ' + str(large[0])):>18}  {'YES' if blind else 'no'}")

print()
if found:
    print(f"BLIND SPOT DEMONSTRATED on {len(found)} board(s):")
    for fen, sm, lg in found:
        print(f"  {fen}: small budget mate {sm} (PV passes the filter), large budget mate {lg} - so the")
        print(f"     passing score overstates the distance by {sm - lg} move(s).")
    print("This turns the caveat into a demonstrated limit, and says how to use the filter: it REMOVES bad scores,")
    print("it does not certify distances - a distance claim needs a deep search, not the filter.")
else:
    print("Not demonstrated on these boards. The caveat stands as a caveat: the filter's accept condition was not")
    print("shown to pass a wrong distance here, which is weaker than 'it cannot'.")
