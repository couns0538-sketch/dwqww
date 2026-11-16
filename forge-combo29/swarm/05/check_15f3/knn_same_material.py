#!/usr/bin/env python3
"""knn_same_material.py EXE -- does `DeadMaterial true` decide from MATERIAL ALONE?

Every position below has the SAME signature KNNk (white K + two knights, black K) and is asserted to be exactly
that by python-chess before it is used. If the switch is a pure material test, either all of them zero or none do.
If they differ, the switch looks at the position and "material alone" is the wrong description.

The same is done for KNNNk (white K + three knights, black K), where mate IS forceable, so a zero there would be
a rule-level error.
"""
import re
import subprocess
import sys

import chess

EXE = sys.argv[1] if len(sys.argv) > 1 else "/tmp/build-rel/forge"
DEPTH = 10
BASE = ["setoption name Threads value 1", "setoption name Hash value 16"]
S14 = ["setoption name LmrQuietBase value 93", "setoption name LmrQuietDivisor value 205",
       "setoption name LmrNoisyBase value 13", "setoption name LmrNoisyDivisor value 333",
       "setoption name LmrHistoryDivisor value 5643", "setoption name NullMoveBase value 5",
       "setoption name LmpBase value 8", "setoption name HistoryPruneMultiplier value 2220",
       "setoption name HistoryBonusQuadratic value 24", "setoption name HistoryBonusLinear value 54",
       "setoption name HistoryBonusMax value 2212", "setoption name SingularDepth value 6",
       "setoption name IirDepth value 2", "setoption name NonPawnCorrection value true"]

# KNNk: white king, two white knights, black king. Eight genuinely different placements.
KNN = [
    ("near corner, knights together", "7k/8/8/8/8/8/8/K1N1N3 w - - 0 1"),
    ("knights split a1/h1",          "7k/8/8/8/8/8/8/KN4N1 w - - 0 1"),
    ("knights centre",               "7k/8/8/3N4/4N3/8/8/K7 w - - 0 1"),
    ("black king centre",            "8/8/3k4/8/3N4/4N3/8/K7 w - - 0 1"),
    ("knights a8/b8",                "NN5k/8/8/8/8/8/8/K7 w - - 0 1"),
    ("knights h8/g8",                "k5NN/8/8/8/8/8/8/K7 w - - 0 1"),
    ("knights e4/f4",                "7k/8/8/8/4NN2/8/8/K7 w - - 0 1"),
    ("knights d5/e5",                "7k/8/8/3NN3/8/8/8/K7 w - - 0 1"),
]
# KNNNk: three knights, mate IS forceable.
KNNN = [
    ("three together",  "7k/8/8/8/8/8/8/K1NNN3 w - - 0 1"),
    ("three split",     "7k/8/8/8/8/N7/N7/K5N1 w - - 0 1"),
    ("three centre",    "7k/8/8/3N4/3NN3/8/8/K7 w - - 0 1"),
]


def signature(b):
    w = "".join(sorted(p.symbol() for p in b.piece_map().values() if p.color))
    bl = "".join(sorted(p.symbol() for p in b.piece_map().values() if not p.color))
    return w + bl


def search(fen, deadmat):
    opts = BASE + S14 + [f"setoption name DeadMaterial value {'true' if deadmat else 'false'}"]
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         text=True, bufsize=1)
    out = []

    def send(s):
        p.stdin.write(s + "\n")
        p.stdin.flush()

    send("uci")
    for o in opts:
        send(o); send("isready")
    send("ucinewgame"); send("isready")
    send(f"position fen {fen}"); send("isready")
    send(f"go depth {DEPTH}")
    bad = False
    while True:
        line = p.stdout.readline()
        if line == "":
            break
        line = line.rstrip("\n")
        out.append(line)
        if any(b in line for b in ("unknown option", "invalid value", "invalid FEN")):
            bad = True
            break
        if line.startswith("bestmove"):
            break
    send("quit")
    try:
        p.wait(timeout=15)
    except subprocess.TimeoutExpired:
        p.kill()
    if bad:
        return None, "HARNESS_STOP"
    pv = [l for l in out if re.search(r"\binfo\b.*\bpv\b", l)]
    if not pv:
        return None, "NO_PV_LINE"
    m = re.search(r"score (mate|cp) (-?\d+)", pv[-1])
    if not m:
        return None, "NO_SCORE"
    return (m.group(1), int(m.group(2))), pv[-1]


fails = []


def need(c, m):
    if not c:
        fails.append(m)
        print(f"  !! FAIL-LOUD: {m}")


def run_set(name, rows, want_sig):
    print(f"########## {name}  (every FEN asserted to have signature {want_sig})")
    print("| placement | fen | sig | DM false | DM true | zeroed by switch? |")
    print("|---|---|---|---|---|---|")
    res = []
    for label, fen in rows:
        b = chess.Board(fen)
        sig = signature(b)
        need(b.is_valid(), f"{name}/{label}: FEN is not legal")
        need(sig == want_sig, f"{name}/{label}: signature is {sig}, expected {want_sig}")
        off, _ = search(fen, False)
        on, _ = search(fen, True)
        need(off is not None, f"{name}/{label}: no score with DeadMaterial false")
        need(on is not None, f"{name}/{label}: no score with DeadMaterial true")
        if off is None or on is None:
            continue
        zeroed = (on[0] == "cp" and on[1] == 0) and not (off[0] == "cp" and off[1] == 0)
        res.append((label, off, on, zeroed))
        print(f"| {label} | {fen} | {sig} | {off[0]} {off[1]} | {on[0]} {on[1]} | {zeroed} |")
    n_zero = sum(1 for r in res if r[3])
    print(f"  => {n_zero} of {len(res)} zeroed by the switch")
    print()
    return res


r1 = run_set("KNNk (two knights)", KNN, "KNNk")
r2 = run_set("KNNNk (three knights)", KNNN, "KNNNk")

print("=" * 90)
if fails:
    print(f"RESULT: {len(fails)} ASSERTION FAILURE(S) — the material of my positions was not what I claimed:")
    for f_ in fails:
        print("  -", f_)
    sys.exit(1)

n1 = sum(1 for r in r1 if r[3])
n2 = sum(1 for r in r2 if r[3])
print(f"KNNk : the switch zeroed {n1} of {len(r1)} positions with IDENTICAL material.")
if 0 < n1 < len(r1):
    print("       => the decision is NOT a function of material alone (same signature, different outcome).")
elif n1 == len(r1):
    print("       => every KNNk position was zeroed: consistent with a pure material key for exactly two knights.")
else:
    print("       => no KNNk position was zeroed: the switch did not act on this material here.")
print(f"KNNNk: the switch zeroed {n2} of {len(r2)} positions. Three knights CAN force mate, so any zero here")
print("       would be a rule-level error, not a matter of evaluation taste.")
print()
print("RESULT: every position asserted to the stated material before use; every score parsed from a real")
print("        info/pv line; a missing line or wrong material fails loudly above.")
