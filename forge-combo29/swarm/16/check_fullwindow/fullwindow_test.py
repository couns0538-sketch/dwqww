#!/usr/bin/env python3
"""fullwindow_test.py EXE OUT.txt : does a full-window root (no accumulated alpha, no root fail-high) restore
mirror symmetry, and what does it cost in nodes?

For each position and its colour mirror, at depths 1, 2, 4, 6:
  * base root (FullWindowRoot false): node count, score, bestmove
  * full-window root (FullWindowRoot true): node count, score, bestmove
and reports, per depth: how many mirror pairs have equal nodes / equal score / equal bestmove, and the median
node cost of the full-window root relative to base.

Every read waits for `bestmove`; stdin is never closed; a missing score raises instead of passing.
"""
import re
import statistics
import subprocess
import sys
import time

import chess

EXE, OUT = sys.argv[1], sys.argv[2]
DEPTHS = [1, 2, 4, 6]
SETS = [("/agent/repos/dwqww/forge-combo29/swarm/16/job2/G_nocastle.fens", 20)]
S14 = [("OwnBook", "false"), ("LmrQuietBase", 93), ("LmrQuietDivisor", 205), ("LmrNoisyBase", 13),
       ("LmrNoisyDivisor", 333), ("LmrHistoryDivisor", 5643), ("NullMoveBase", 5), ("LmpBase", 8),
       ("HistoryPruneMultiplier", 2220), ("HistoryBonusQuadratic", 24), ("HistoryBonusLinear", 54),
       ("HistoryBonusMax", 2212), ("SingularDepth", 6), ("IirDepth", 2), ("NonPawnCorrection", "true")]


class Missing(Exception):
    pass


def search(fen, depth, fullwindow):
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)

    def send(c):
        p.stdin.write(c + "\n")
        p.stdin.flush()

    def to(tok, lim):
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
    for n, v in [("Threads", 1), ("Hash", 16)] + S14:
        send(f"setoption name {n} value {v}")
        send("isready"); to("readyok", 15)
    if fullwindow:
        send("setoption name FullWindowRoot value true")
        send("isready")
        got, ok = to("readyok", 15)
        if not ok:
            raise Missing("FullWindowRoot option not accepted (no readyok)")
        if any("invalid value" in l.lower() or "unknown option" in l.lower() for l in got):
            raise Missing("FullWindowRoot not recognised by this build")
    send("position fen " + fen)
    send("isready"); to("readyok", 15)
    send(f"go depth {depth}")
    lines, ok = to("bestmove", 300)
    send("quit")
    try:
        p.wait(timeout=10)
    except Exception:
        p.kill()
    if not ok:
        raise Missing(f"no bestmove at depth {depth}")
    best = None
    score = None
    nodes = None
    for l in lines:
        if l.startswith("bestmove"):
            best = l.split()[1]
        m = re.search(rf"^info depth {depth} .*score (cp|mate) (-?\d+) nodes (\d+)", l)
        if m:
            score = (m.group(1), int(m.group(2)))
            nodes = int(m.group(3))
    if score is None or nodes is None:
        raise Missing(f"no depth-{depth} info line with score+nodes for {fen}")
    return best, score, nodes


fens = [l.strip() for l in open(SETS[0][0]) if l.strip()][:SETS[0][1]]
out = [f"positions: {len(fens)} from {SETS[0][0]}", f"depths: {DEPTHS}", ""]
print(out[0])

for depth in DEPTHS:
    base = {"eq_nodes": 0, "eq_score": 0, "eq_bm": 0, "n": 0, "nodes": [], "fwnodes": []}
    for fen in fens:
        b = chess.Board(fen)
        mir = b.mirror()
        for fw in (False, True):
            ba, sa, na = search(fen, depth, fw)
            bb, sb, nb = search(mir.fen(), depth, fw)
            # map the mirror bestmove back
            back = None
            if bb and bb != "0000":
                mv = chess.Move.from_uci(bb)
                back = chess.Move(mv.from_square ^ 56, mv.to_square ^ 56, mv.promotion).uci()
            if fw:
                base["fwnodes"] += [na, nb]
                base["fw_eq_nodes"] = base.get("fw_eq_nodes", 0) + (na == nb)
                base["fw_eq_score"] = base.get("fw_eq_score", 0) + (sa == sb)
                base["fw_eq_bm"] = base.get("fw_eq_bm", 0) + (ba == back)
            else:
                base["nodes"] += [na, nb]
                base["eq_nodes"] += (na == nb)
                base["eq_score"] += (sa == sb)
                base["eq_bm"] += (ba == back)
            base["n"] += 1
    n = len(fens)
    line = (f"depth {depth:2d} | base: nodes equal {base['eq_nodes']:2d}/{n} score equal "
            f"{base['eq_score']:2d}/{n} bm equal {base['eq_bm']:2d}/{n} | full-window: nodes equal "
            f"{base.get('fw_eq_nodes',0):2d}/{n} score equal {base.get('fw_eq_score',0):2d}/{n} bm equal "
            f"{base.get('fw_eq_bm',0):2d}/{n} | median nodes base "
            f"{statistics.median(base['nodes']):7.0f} fw {statistics.median(base['fwnodes']):7.0f}")
    out.append(line)
    print(line)

text = "\n".join(out) + "\n"
with open(OUT, "w") as fh:
    fh.write(text)
