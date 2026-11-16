#!/usr/bin/env python3
"""check_27F12.py EXE : check seat 27's S-F12 — "the clock is ignored when BLACK is to move".

Their claim, verbatim in effect: on `2N3k1/3pn1p1/8/2R1P1KP/7P/8/8/5r2 b - - 18 55`, `go wtime 0 / 1 / 3 / 10 /
50 / 200 / 1000 / 3000` all give the SAME answer (depth 20, 286,156 nodes, ~124 ms), while `go movetime 5` correctly
stops at depth 1. And they say the discriminator is the SIDE TO MOVE: black -> clock ignored, white -> emergency
path with 0 info lines.

My check, written from their claim:
  T1  their exact FEN, wtime swept 0..3000: do the answers agree with each other?
  T2  the same BOARD with `w` to move instead of `b`: does it differ?
  T3  startpos with `b` vs `w`
  T4  `go movetime 5` on their FEN (the control that the movetime path works)
If T1 shows identical depth/nodes for all wtimes AND T2 differs by side-to-move, the claim is confirmed.
"""
import re
import shlex
import subprocess
import sys
import time

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]
PC20 = [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
        ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]
EXE = sys.argv[1]
THEIR_FEN = "2N3k1/3pn1p1/8/2R1P1KP/7P/8/8/5r2 b - - 18 55"


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
    t0 = time.monotonic()
    p.stdin.write(f"{go}\n"); p.stdin.flush()
    lines, best, last = [], None, None
    while True:
        line = p.stdout.readline()
        if not line:
            break
        s = line.rstrip("\n")
        if s.startswith("info depth"):
            lines.append(s)
            last = s
        if s.startswith("bestmove"):
            best = s.split()[-1]
            break
    ms = (time.monotonic() - t0) * 1000.0
    p.stdin.write("quit\n"); p.stdin.flush()
    try:
        p.wait(timeout=20)
    except subprocess.TimeoutExpired:
        p.kill()
    d = re.search(r"depth (\d+)", last or "")
    n = re.search(r"nodes (\d+)", last or "")
    return {"infos": len(lines), "depth": int(d.group(1)) if d else 0,
            "nodes": int(n.group(1)) if n else 0, "move": best, "ms": round(ms)}


print(f"### check of seat 27 S-F12 — {EXE} (PC20, Threads 1, Hash 16)")
print()
print("T1: their FEN (BLACK to move), wtime swept")
print(f"{'command':<22} {'infos':>6} {'depth':>6} {'nodes':>9} {'ms':>6} {'move':>6}")
t1 = []
for w in (0, 1, 3, 10, 50, 200, 1000, 3000):
    r = run(THEIR_FEN, f"go wtime {w} btime {w} winc 0 binc 0")
    t1.append((w, r))
    print(f"{'go wtime ' + str(w):<22} {r['infos']:>6} {r['depth']:>6} {r['nodes']:>9} {r['ms']:>6} {str(r['move']):>6}")

same = len({(r['depth'], r['nodes'], r['move']) for _, r in t1}) == 1
print()
print(f"T1 verdict: all wtime values give the SAME depth/nodes/move? {same}  <- their claim says True")

print()
print("T2: the same BOARD with WHITE to move")
WHITE_FEN = "2N3k1/3pn1p1/8/2R1P1KP/7P/8/8/5r2 w - - 18 55"
r = run(WHITE_FEN, "go wtime 0 btime 0 winc 0 binc 0")
print(f"  go wtime 0 -> infos {r['infos']}, depth {r['depth']}, nodes {r['nodes']}, move {r['move']}, {r['ms']} ms")
w0 = r

print()
print("T3: startpos, black vs white")
for label, fen in (("startpos b", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR b KQkq - 0 1"),
                   ("startpos w", "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1")):
    r = run(fen, "go wtime 0 btime 0 winc 0 binc 0")
    print(f"  {label:<12} go wtime 0 -> infos {r['infos']}, depth {r['depth']}, nodes {r['nodes']}, move {r['move']}")

print()
print("T4: control — go movetime 5 on their FEN")
r = run(THEIR_FEN, "go movetime 5")
print(f"  go movetime 5 -> infos {r['infos']}, depth {r['depth']}, nodes {r['nodes']}, move {r['move']}, {r['ms']} ms")

print()
print("SUMMARY")
print(f"  black-to-move clock ignored (all wtimes identical): {same}")
print(f"  white-to-move at wtime 0: infos {w0['infos']} (their claim: 0 info lines = emergency path)")
print(f"  movetime control: depth {r['depth']} (their claim: stops at depth 1)")
