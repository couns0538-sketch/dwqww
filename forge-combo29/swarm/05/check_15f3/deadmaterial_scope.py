#!/usr/bin/env python3
"""deadmaterial_scope.py EXE -- follow-up to S-C5: does `DeadMaterial true` decide from MATERIAL ALONE, or does it
look at the position?

If it is a pure material test ("two knights and nothing else = dead"), then it must also zero positions where the
two knights are far apart and mate is impossible, AND it must zero a three-knight position, which is NOT dead
(three knights CAN force mate in the corner). If it looks at the position, a three-knight position should keep a
non-zero score.

Sets, all built here with python-chess and asserted before use:
  A  two knights + kings, knights deliberately far apart, side to move with no immediate tactics   (dead)
  B  THREE knights + kings                                                                          (NOT dead)
  C  two knights + one black pawn                                                                   (NOT dead)
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
SETS = {
    "A two knights (dead)": [
        "8/8/8/8/8/8/8/K1N1N2k w - - 0 1",
        "8/8/8/8/8/8/1n6/K1N4k w - - 0 1",
        "8/8/8/8/8/8/6n1/K1N4k w - - 0 1",
        "N7/8/8/8/8/8/8/K6k w - - 0 1",
    ],
    "B three knights (NOT dead)": [
        "8/8/8/8/8/8/8/K1NNN2k w - - 0 1",
        "8/8/8/8/8/8/8/KN1N3k w - - 0 1",
        "N7/8/8/8/8/8/1N6/K1N4k w - - 0 1",
    ],
    "C two knights + black pawn (NOT dead)": [
        "8/8/8/8/8/7p/8/K1N1N2k w - - 0 1",
        "8/8/8/8/8/8/5p2/K1N1N2k w - - 0 1",
    ],
}


def search(fen, deadmat):
    opts = BASE + S14 + ([f"setoption name DeadMaterial value {'true' if deadmat else 'false'}"])
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
    stop = False
    while True:
        line = p.stdout.readline()
        if line == "":
            break
        line = line.rstrip("\n")
        out.append(line)
        if any(b in line for b in ("unknown option", "invalid value", "invalid FEN")):
            stop = True
            break
        if line.startswith("bestmove"):
            break
    send("quit")
    try:
        p.wait(timeout=15)
    except subprocess.TimeoutExpired:
        p.kill()
    if stop:
        return "HARNESS_STOP"
    pv = [l for l in out if re.search(r"\binfo\b.*\bpv\b", l)]
    if not pv:
        return "NO_PV"                      # absent parse is NOT a score
    m = re.search(r"score (mate|cp) (-?\d+)", pv[-1])
    if not m:
        return "NO_SCORE"
    return f"{m.group(1)} {m.group(2)}"


print(f"exe: {EXE}   go depth {DEPTH}   S14")
print()
print("| set | fen | DeadMaterial false | DeadMaterial true | python-chess insuff. material? |")
print("|---|---|---|---|---|")
fail = 0
for setname, fens in SETS.items():
    for fen in fens:
        b = chess.Board(fen)
        if not b.is_valid():
            print(f"| {setname} | {fen} | INVALID FEN — skipped | | |")
            fail += 1
            continue
        a = search(fen, False)
        c = search(fen, True)
        for v in (a, c):
            if v in ("HARNESS_STOP", "NO_PV", "NO_SCORE"):
                print(f"| {setname} | {fen} | FAIL-LOUD {v} | FAIL-LOUD {v} | |")
                fail += 1
        insuff = b.is_insufficient_material()
        print(f"| {setname} | {fen} | {a} | {c} | {insuff} |")
print()
if fail:
    print(f"RESULT: {fail} position(s) could not be measured — no conclusion from this run")
    sys.exit(1)
print("RESULT: every position produced a parsed score for both settings.")
print("Reading it: if set B (three knights, which CAN mate) is also cp 0 with DeadMaterial true,")
print("the switch is a pure material test that is WRONG about three knights; if B stays non-zero,")
print("the switch inspects the position and A being 0 is well-founded.")
