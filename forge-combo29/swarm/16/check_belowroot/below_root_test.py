#!/usr/bin/env python3
"""below_root_test.py EXE OUT.txt : which below-root component creates the depth-2 asymmetry?

Instrument: the position/mirror pair whose depth-2 full-window counts are 336 vs 334. At depth 2 the root's
alpha is removed (full-window root) and the asymmetry still appears, so it is created below the root.
Every search: fresh process, `ucinewgame` before it, OwnBook false (seat 10's cold discipline).

Configurations, each isolating one candidate:
  baseline16     Hash 16, S14 (the 336 vs 334 reference)
  hash1          Hash 1  - a table too small to hold the tree
  hash2048       Hash 2048 - the other extreme (a control: if size does not matter, this matches too)
  nohist         HistoryBonusLinear 0 + HistoryBonusQuadratic 0 (history gains zeroed)
  histmax1       HistoryBonusMax 100 (history clamped to its minimum)
  noprune        HistoryPruneDepth 0 (history pruning off)
  nolmrhist      LmrHistoryDivisor 30000 (history's LMR influence minimised)
  no4ply         ContHist4PlyRead false (already default; explicit for completeness)
  nothreat       ThreatHistory false (already default; explicit)

Reports nodes for A and the mirror under every configuration, plus whether they are equal.
"""
import re
import subprocess
import sys
import time

import chess

EXE, OUT = sys.argv[1], sys.argv[2]
FEN = "R7/8/8/5p1p/5K1P/1kpr2n1/8/8 b - - 0 1"
MIR = chess.Board(FEN).mirror().fen()
DEPTH = 2
S14 = [("LmrQuietBase", 93), ("LmrQuietDivisor", 205), ("LmrNoisyBase", 13), ("LmrNoisyDivisor", 333),
       ("LmrHistoryDivisor", 5643), ("NullMoveBase", 5), ("LmpBase", 8), ("HistoryPruneMultiplier", 2220),
       ("HistoryBonusQuadratic", 24), ("HistoryBonusLinear", 54), ("HistoryBonusMax", 2212),
       ("SingularDepth", 6), ("IirDepth", 2), ("NonPawnCorrection", "true")]

CONFIGS = [
    ("baseline16", {"Hash": 16}),
    ("hash1", {"Hash": 1}),
    ("hash2048", {"Hash": 2048}),
    ("nohist", {"Hash": 16, "HistoryBonusLinear": 0, "HistoryBonusQuadratic": 0}),
    ("histmax100", {"Hash": 16, "HistoryBonusMax": 100}),
    ("noprune", {"Hash": 16, "HistoryPruneDepth": 0}),
    ("nolmrhist", {"Hash": 16, "LmrHistoryDivisor": 30000}),
    ("no4ply", {"Hash": 16, "ContHist4PlyRead": "false"}),
    ("nothreat", {"Hash": 16, "ThreatHistory": "false"}),
    # combinations prompted by nohist narrowing the gap from 12 to 3
    ("nohist_noprune", {"Hash": 16, "HistoryBonusLinear": 0, "HistoryBonusQuadratic": 0,
                        "HistoryPruneDepth": 0}),
    ("nohist_nolmr", {"Hash": 16, "HistoryBonusLinear": 0, "HistoryBonusQuadratic": 0,
                      "LmrHistoryDivisor": 30000}),
    ("nohist_hash1", {"Hash": 1, "HistoryBonusLinear": 0, "HistoryBonusQuadratic": 0}),
    ("nohist_max0", {"Hash": 16, "HistoryBonusLinear": 0, "HistoryBonusQuadratic": 0,
                     "HistoryBonusMax": 100, "HistoryPruneDepth": 0, "LmrHistoryDivisor": 30000}),
]


class Missing(Exception):
    pass


def search(fen, opts):
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)

    def send(c):
        p.stdin.write(c + "\n")
        p.stdin.flush()

    def to(tok, lim=180):
        out = []
        dl = time.monotonic() + lim
        while time.monotonic() < dl:
            l = p.stdout.readline()
            if not l:
                return out, False
            l = l.rstrip("\n")
            out.append(l)
            if l.strip().startswith(tok):
                return out, True
        return out, False

    send("uci"); to("uciok", 15)
    send("isready"); to("readyok", 15)
    send("setoption name OwnBook value false")
    send("isready"); to("readyok", 15)
    send("setoption name FullWindowRoot value true")
    send("isready")
    got, ok = to("readyok", 15)
    if not ok or any("unknown option" in l.lower() for l in got):
        raise Missing("FullWindowRoot not accepted")
    # S14 first, then the configuration's overrides
    for n, v in S14:
        send(f"setoption name {n} value {v}")
        send("isready")
        got, ok = to("readyok", 15)
        for l in got:
            if "invalid value" in l.lower() or "unknown option" in l.lower():
                raise Missing(f"option rejected: {l}")
    for n, v in opts.items():
        send(f"setoption name {n} value {v}")
        send("isready")
        got, ok = to("readyok", 15)
        for l in got:
            if "invalid value" in l.lower() or "unknown option" in l.lower():
                raise Missing(f"option rejected: {l}")
    send("ucinewgame")
    send("isready"); to("readyok", 15)
    send("position fen " + fen)
    send("isready"); to("readyok", 15)
    send(f"go depth {DEPTH}")
    lines, ok = to("bestmove", 300)
    send("quit")
    try:
        p.wait(timeout=10)
    except Exception:
        p.kill()
    if not ok:
        raise Missing("no bestmove")
    nodes = score = None
    for l in lines:
        m = re.search(rf"^info depth {DEPTH} .*score (cp|mate) (-?\d+) nodes (\d+)", l)
        if m:
            score = f"{m.group(1)} {m.group(2)}"
            nodes = int(m.group(3))
    if nodes is None:
        raise Missing("no depth info line")
    return nodes, score


out = [f"position {FEN}", f"mirror   {MIR}", f"depth {DEPTH}, full-window root, cold (ucinewgame each)", ""]
for name, opts in CONFIGS:
    try:
        na, sa = search(FEN, opts)
        nb, sb = search(MIR, opts)
        line = (f"{name:12s} {opts} | A {na:5d} nodes {sa:10s} | mirror {nb:5d} nodes {sb:10s} | "
                f"nodes equal {na == nb}")
    except Missing as exc:
        line = f"{name:12s} {opts} | NOT MEASURED: {exc}"
    out.append(line)
    print(line)
text = "\n".join(out) + "\n"
with open(OUT, "w") as fh:
    fh.write(text)
