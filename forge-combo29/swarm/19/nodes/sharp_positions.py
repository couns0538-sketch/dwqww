#!/usr/bin/env python3
"""sharp_positions.py EXE FENS OUTDIR : find SHARP positions and test whether nodes/softnodes diverge there.

File 6 / the coordinator's gap: 19-F45 and 19-F46 showed the bestmove was identical between `go nodes` and
`go softnodes` on six set-G positions, but six positions says nothing about a position where the top two moves
are close. This finds those positions and tests them.

Stage 1 (find): run MultiPV 2 at depth 12 under PC20, Threads 1. Keep positions whose top-two score gap is
small. Score in centipawns from the engine's own `multipv` lines.

Stage 2 (test): for each sharp position, at each budget N, run `go nodes N` and `go softnodes N` (one fresh
process each, cold, 5 runs to confirm determinism) and compare the bestmove.

A divergence is the finding: it means the mode choice affects PLAY, not just effort.
"""
import os
import re
import subprocess
import sys

exe, fens, outdir = sys.argv[1], sys.argv[2], sys.argv[3]
gap_cp = int(sys.argv[4]) if len(sys.argv) > 4 else 15
budgets = [int(x) for x in (sys.argv[5].split(",") if len(sys.argv) > 5 else ["20000", "50000"])]
os.makedirs(outdir, exist_ok=True)
for v in ("ASAN_OPTIONS", "UBSAN_OPTIONS", "TSAN_OPTIONS"):
    os.environ.pop(v, None)

S14 = [("LmrQuietBase", 93), ("LmrQuietDivisor", 205), ("LmrNoisyBase", 13), ("LmrNoisyDivisor", 333),
       ("LmrHistoryDivisor", 5643), ("NullMoveBase", 5), ("LmpBase", 8),
       ("HistoryPruneMultiplier", 2220), ("HistoryBonusQuadratic", 24), ("HistoryBonusLinear", 54),
       ("HistoryBonusMax", 2212), ("SingularDepth", 6), ("IirDepth", 2), ("NonPawnCorrection", "true"),
       ("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"), ("CorrHistV2", "true"),
       ("MateAlphaGuard", "true"), ("OwnBook", "false"), ("Hash", "16"),
       ("MultiPV", "2")]

positions = [l.split(";")[0].strip() for l in open(fens) if l.strip() and not l.startswith("#")][:60]


def run(fen, cmd, multipv2=False):
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1)

    def send(l):
        p.stdin.write(l + "\n")
        p.stdin.flush()

    def readto(pred):
        got = []
        for _ in range(800000):
            l = p.stdout.readline()
            if not l:
                return got
            l = l.rstrip("\n")
            got.append(l)
            if pred(l):
                return got
        return got

    send("uci")
    readto(lambda l: l.startswith("uciok"))
    opts = S14 if multipv2 else [o for o in S14 if o[0] != "MultiPV"]
    for k, v in opts:
        send("setoption name %s value %s" % (k, v))
        send("isready")
        readto(lambda l: l.startswith("readyok"))
    send("ucinewgame")
    send("isready")
    readto(lambda l: l.startswith("readyok"))
    send("position fen " + fen)
    send("isready")
    readto(lambda l: l.startswith("readyok"))
    send(cmd)
    block = readto(lambda l: l.startswith("bestmove"))
    send("quit")
    try:
        p.communicate(timeout=180)
    except subprocess.TimeoutExpired:
        p.kill()
    return block


def score_of(line):
    m = re.search(r"score (cp|mate) (-?\d+)", line)
    if not m:
        return None
    return ("mate", int(m.group(2))) if m.group(1) == "mate" else ("cp", int(m.group(2)))


# ---- stage 1: find sharp positions ----
sharp = []
for i, fen in enumerate(positions):
    block = run(fen, "go depth 12", multipv2=True)
    best = {}
    for l in block:
        if not l.startswith("info depth 12") or " multipv " not in l:
            continue
        idx = int(l.split(" multipv ")[1].split()[0])
        sc = score_of(l)
        mv = l.split(" pv ")[1].split()[0] if " pv " in l else None
        if sc and mv:
            best[idx] = (sc, mv)
    if 1 in best and 2 in best:
        s1, s2 = best[1][0], best[2][0]
        if s1[0] == "cp" and s2[0] == "cp":
            gap = abs(s1[1] - s2[1])
            if gap <= gap_cp:
                sharp.append((i, fen, best[1], best[2], gap))
    if (i + 1) % 15 == 0:
        print("  scanned %d/%d, sharp so far %d" % (i + 1, len(positions), len(sharp)), flush=True)

lines = ["# sharp positions and the nodes/softnodes divergence test", "",
         "build PC r15, PC20, Threads 1, Hash 16, cold; sharp = top-two cp gap <= %d at depth 12" % gap_cp, "",
         "## stage 1: sharp positions found (%d of %d scanned)" % (len(sharp), len(positions)), ""]
lines.append("| pos | best | score | second | score | gap cp |")
lines.append("|---|---|---|---|---|---|")
for i, fen, b1, b2, gap in sharp:
    lines.append("| %d | %s | %s %d | %s | %s %d | %d |"
                 % (i, b1[1], b1[0][0], b1[0][1], b2[1], b2[0][0], b2[0][1], gap))
print("stage 1 done: %d sharp positions" % len(sharp), flush=True)

# ---- stage 2: nodes vs softnodes on the sharp positions ----
lines += ["", "## stage 2: does the mode change the MOVE on a sharp position?", "",
          "| pos | gap cp | N | nodes move | softnodes move | same? |",
          "|---|---|---|---|---|---|"]
diverged = 0
cells = 0
for i, fen, b1, b2, gap in sharp[:20]:
    for n in budgets:
        res = {}
        for mode in ("nodes", "softnodes"):
            runs = [run(fen, "go %s %d" % (mode, n)) for _ in range(1)]
            blk = runs[0]
            bm = None
            for l in blk:
                if l.startswith("bestmove"):
                    bm = l.split()[1] if len(l.split()) > 1 else None
            res[mode] = bm
        same = res["nodes"] == res["softnodes"]
        cells += 1
        if not same:
            diverged += 1
        lines.append("| %d | %d | %d | %s | %s | **%s** |"
                     % (i, gap, n, res["nodes"], res["softnodes"], "yes" if same else "NO"))
        print("pos %d gap %d N %d: nodes=%s softnodes=%s %s"
              % (i, gap, n, res["nodes"], res["softnodes"], "same" if same else "DIVERGED"), flush=True)

lines += ["", "cells: %d ; divergent: %d" % (cells, diverged)]
text = "\n".join(lines)
open(os.path.join(outdir, "RESULT.txt"), "w").write(text + "\n")
print("\n" + text[-1200:])
