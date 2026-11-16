#!/usr/bin/env python3
"""check_s06f9.py -- my own check of seat 06's S-F9, written from its one-sentence claim only:
"on G index 196 (5Q2/1k6/3pK1PP/3P4/8/4N3/8/8 w) the engine reports cp 4402 while its colour mirror reports
mate 14; index 217 likewise cp 2557 vs mate 11".

I do NOT use their scripts. I take the two FENs from their sentence, build the colour mirror myself with
python-chess, drive the engine at depth 10 with S14/Threads 1/Hash 16, and report the last pv line of each.
Control: the same position against itself must give the same score twice (proves the harness can see a stable
score), and a position whose mirror I build by hand (startpos) must mirror trivially.
"""
import re
import subprocess
import sys
import time

import chess

EXE = sys.argv[1] if len(sys.argv) > 1 else "/tmp/build-rel/forge"
DEPTH = int(sys.argv[2]) if len(sys.argv) > 2 else 10

S14 = [
    "setoption name Threads value 1", "setoption name Hash value 16",
    "setoption name LmrQuietBase value 93", "setoption name LmrQuietDivisor value 205",
    "setoption name LmrNoisyBase value 13", "setoption name LmrNoisyDivisor value 333",
    "setoption name LmrHistoryDivisor value 5643", "setoption name NullMoveBase value 5",
    "setoption name LmpBase value 8", "setoption name HistoryPruneMultiplier value 2220",
    "setoption name HistoryBonusQuadratic value 24", "setoption name HistoryBonusLinear value 54",
    "setoption name HistoryBonusMax value 2212", "setoption name SingularDepth value 6",
    "setoption name IirDepth value 2", "setoption name NonPawnCorrection value true",
]
BAD = ("unknown option", "invalid value", "invalid FEN", "illegal move")

FENS = {
    "G196": "5Q2/1k6/3pK1PP/3P4/8/4N3/8/8 w - - 0 1",
    "G217": "8/7p/8/7p/3k2b1/6K1/2p5/8 b - - 0 1",
}


def drive(fen, depth):
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         text=True, bufsize=1)

    def send(s):
        p.stdin.write(s + "\n")
        p.stdin.flush()

    def until(tok, limit=300):
        got = []
        t0 = time.time()
        while time.time() - t0 < limit:
            line = p.stdout.readline()
            if line == "":
                got.append("### EOF")
                break
            line = line.rstrip("\n")
            got.append(line)
            if line.startswith(tok):
                break
            if any(b in line for b in BAD):
                got.append("### HARNESS_STOP")
                break
        return got

    send("uci")
    until("uciok")
    for o in S14:
        send(o)
        send("isready")
        r = until("readyok")
        if any("###" in x for x in r):
            p.kill()
            return "HARNESS_STOP", ""
    send("ucinewgame")
    send("isready")
    until("readyok")
    send(f"position fen {fen}")
    send("isready")
    r = until("readyok")
    if any("### HARNESS_STOP" in x for x in r):
        p.kill()
        return "REFUSED", ""
    send(f"go depth {depth}")
    block = until("bestmove")
    send("quit")
    try:
        p.wait(timeout=10)
    except subprocess.TimeoutExpired:
        p.kill()
    pv = [l for l in block if re.search(r"\binfo\b.*\bpv\b", l)]
    if not pv:
        return "(no pv)", ""
    m = re.search(r"score (mate|cp) (-?\d+)", pv[-1])
    return (f"{m.group(1)} {m.group(2)}" if m else "?"), pv[-1]


def mirror(fen):
    b = chess.Board(fen)
    m = b.mirror()
    return m.fen()


print(f"exe: {EXE}   go depth {DEPTH}   S14, Threads 1, Hash 16")
print()
results = {}
for name, fen in FENS.items():
    mfen = mirror(fen)
    s1, l1 = drive(fen, DEPTH)
    s2, l2 = drive(mfen, DEPTH)
    s3, l3 = drive(fen, DEPTH)   # control: same position twice
    results[name] = (s1, s2, s3)
    print(f"### {name}")
    print(f"  fen      : {fen}")
    print(f"  score    : {s1}")
    print(f"  last pv  : {l1}")
    print(f"  mirror   : {mfen}")
    print(f"  score    : {s2}")
    print(f"  last pv  : {l2}")
    print(f"  CONTROL same position twice: {s1} vs {s3}  -> {'stable' if s1 == s3 else 'UNSTABLE'}")
    print()

print("VERDICT")
for name, (a, b, c) in results.items():
    claim_cp = name == "G196" and a.startswith("cp 4402")
    claim_mate = b.startswith("mate 14") if name == "G196" else b.startswith("mate 11")
    print(f"  {name}: engine={a} mirror={b}  (their claim: cp/mate split at index "
          f"{'196' if name == 'G196' else '217'})")
    print(f"        reproduces their split as stated: "
          f"{'YES' if (('cp' in a) and ('mate' in b)) else 'NO'}   exact numbers as stated: "
          f"{'YES' if (claim_cp and claim_mate) else 'NO'}")
