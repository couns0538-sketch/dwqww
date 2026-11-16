#!/usr/bin/env python3
"""what_makes_flat.py EXE -- narrows S-F14: which property of a position makes the fifty-move boundary FLAT
(seat 25's middlegame: flat 99) instead of the bare-endgame law (counter+depth ~100)?

Two candidate properties, each tested by a single change to one board:
  T1 CASTLING RIGHTS present?   (bare endgames have none)
  T2 PIECES THAT CAN BE CAPTURED / pawns present?  (already tested: stripping pawns gave flat 100)

Test board: the bare-endgame K+R vs K, which DOES follow the law. Then add back one property at a time and see
whether the boundary stops tracking depth.
"""
import re
import subprocess
import sys

import chess

EXE = sys.argv[1] if len(sys.argv) > 1 else "/tmp/build-rel/forge"
S14 = ["setoption name Threads value 1", "setoption name Hash value 16",
       "setoption name LmrQuietBase value 93", "setoption name LmrQuietDivisor value 205",
       "setoption name LmrNoisyBase value 13", "setoption name LmrNoisyDivisor value 333",
       "setoption name LmrHistoryDivisor value 5643", "setoption name NullMoveBase value 5",
       "setoption name LmpBase value 8", "setoption name HistoryPruneMultiplier value 2220",
       "setoption name HistoryBonusQuadratic value 24", "setoption name HistoryBonusLinear value 54",
       "setoption name HistoryBonusMax value 2212", "setoption name SingularDepth value 6",
       "setoption name IirDepth value 2", "setoption name NonPawnCorrection value true"]


def with_clock(fen, c):
    q = fen.split()
    q[4] = str(c)
    return " ".join(q)


def run(fen, depth):
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         text=True, bufsize=1)
    out = []

    def send(s):
        p.stdin.write(s + "\n")
        p.stdin.flush()

    send("uci")
    for o in S14:
        send(o); send("isready")
    send("ucinewgame"); send("isready")
    send(f"position fen {fen}"); send("isready")
    send(f"go depth {depth}")
    while True:
        line = p.stdout.readline()
        if line == "":
            break
        line = line.rstrip("\n")
        out.append(line)
        if any(b in line for b in ("unknown option", "invalid value", "invalid FEN")):
            send("quit"); p.kill()
            return None
        if line.startswith("bestmove"):
            break
    send("quit")
    try:
        p.wait(timeout=20)
    except subprocess.TimeoutExpired:
        p.kill()
    pv = [l for l in out if re.search(r"\binfo\b.*\bpv\b", l)]
    if not pv:
        return None
    m = re.search(r"score (mate|cp) (-?\d+)", pv[-1])
    return f"{m.group(1)} {m.group(2)}" if m else None


def boundary(fen, depth, lo=60, hi=100):
    for c in range(lo, hi + 1):
        sc = run(with_clock(fen, c), depth)
        if sc is None:
            return "PARSE-FAIL"
        if sc == "cp 0":
            return c
    return f">{hi}"


BOARDS = {
    "bare K+R (law holds)": "1K6/8/8/3R4/8/8/8/k7 w - - 0 1",
    "same + castling rights": "1K6/8/8/3R4/8/8/8/k7 w KQkq - 0 1",
    "same + a black pawn far away": "1K6/8/8/3R4/8/8/7p/k7 w - - 0 1",
}

print(f"exe: {EXE}")
print()
print("| board | material sig | d6 | d8 | d10 | d12 | flat or tracking? |")
print("|---|---|---|---|---|---|---|")
for label, fen in BOARDS.items():
    b = chess.Board(fen)
    if not b.is_valid():
        print(f"| {label} | INVALID | - | - | - | - | skipped |")
        continue
    sig = "".join(sorted(p.symbol() for p in b.piece_map().values()))
    vals = [boundary(fen, d) for d in (6, 8, 10, 12)]
    ok = all(isinstance(v, int) for v in vals)
    flat = ok and len(set(vals)) == 1
    tracking = ok and len(set(vals)) > 1
    verdict = "FLAT" if flat else ("tracks depth" if tracking else "unclear")
    print(f"| {label} | {sig} | {vals[0]} | {vals[1]} | {vals[2]} | {vals[3]} | {verdict} |")
print()
print("Reading: whichever single change turns 'tracks depth' into 'FLAT' names the property that matters.")
print("If none of them does, the difference is something else and I will say I do not know.")
