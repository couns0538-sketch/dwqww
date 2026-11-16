#!/usr/bin/env python3
"""depthgap.py EXE OUTDIR : does the colour-mirror SCORE gap shrink with depth?

PC build under PC20, Threads 1, Hash 16. For depths 6, 8, 10, 12 on the first N G positions:
search each position and its colour mirror (fresh process + ucinewgame each), compare score and bestmove.
Reports, per depth: score-equal count, median |score gap| (cp-only pairs), p90, and move-mismatch count.
"""
import os
import re
import statistics
import subprocess
import sys
import time

import chess

EXE, OUTDIR = sys.argv[1], sys.argv[2]
os.makedirs(OUTDIR, exist_ok=True)
NPOS = 60
DEPTHS = [6, 8, 10, 12]

S14 = {"LmrQuietBase": 93, "LmrQuietDivisor": 205, "LmrNoisyBase": 13, "LmrNoisyDivisor": 333,
       "LmrHistoryDivisor": 5643, "NullMoveBase": 5, "LmpBase": 8, "HistoryPruneMultiplier": 2220,
       "HistoryBonusQuadratic": 24, "HistoryBonusLinear": 54, "HistoryBonusMax": 2212,
       "SingularDepth": 6, "IirDepth": 2, "NonPawnCorrection": "true"}
PC20 = {**S14, "CuckooRep": "true", "HistRework": 2, "TtPruneV2": "true", "CorrHistV2": "true",
        "MateAlphaGuard": "true", "OwnBook": "false", "Threads": 1, "Hash": 16}


class Missing(Exception):
    pass


def search(fen, depth):
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)

    def send(c):
        p.stdin.write(c + "\n")
        p.stdin.flush()

    def to(tok, lim=300):
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

    send("uci"); uci, ok = to("uciok", 20)
    if not ok:
        raise Missing("no uciok")
    known = {m.group(1) for l in uci for m in [re.match(r"option name (.*) type ", l)] if m}
    send("isready"); to("readyok", 20)
    for n, v in PC20.items():
        if n not in known:
            raise Missing(f"option {n} absent")
        send(f"setoption name {n} value {v}")
        send("isready"); to("readyok", 20)
    send("ucinewgame"); send("isready"); to("readyok", 20)
    send("position fen " + fen); send("isready"); to("readyok", 20)
    send(f"go depth {depth}")
    lines, ok = to("bestmove", 300)
    send("quit")
    try:
        p.wait(timeout=10)
    except Exception:
        p.kill()
    if not ok:
        raise Missing("no bestmove")
    best = None
    kind = val = None
    for l in lines:
        if l.startswith("bestmove"):
            best = l.split()[1]
        m = re.search(rf"^info depth {depth} .*score (cp|mate) (-?\d+)", l)
        if m:
            kind, val = m.group(1), int(m.group(2))
    if best is None or kind is None:
        raise Missing("missing bestmove or score")
    return best, kind, val


def back(mv):
    if not mv or mv == "0000":
        return None
    m = chess.Move.from_uci(mv)
    return chess.Move(m.from_square ^ 56, m.to_square ^ 56, m.promotion).uci()


fens = [l.strip() for l in open("/agent/repos/dwqww/forge-combo29/swarm/16/depthgap/G_nocastle.fens")
        if l.strip()][:NPOS]
out = [f"exe {EXE}", f"positions {len(fens)} (first of G_nocastle)", "PC20 + Threads 1 + Hash 16, cold per search", ""]
print(out[0])
for depth in DEPTHS:
    eq = 0
    gaps = []
    bmmis = 0
    n = 0
    for fen in fens:
        mir = chess.Board(fen).mirror().fen()
        try:
            ba, ka, va = search(fen, depth)
            bb, kb, vb = search(mir, depth)
        except Missing:
            continue
        n += 1
        if (ka, va) == (kb, vb):
            eq += 1
        elif ka == "cp" and kb == "cp":
            gaps.append(abs(va - vb))
        if ba != back(bb):
            bmmis += 1
    gaps.sort()
    line = (f"depth {depth:2d} | n {n:3d} | score_equal {eq:3d} | median |gap| "
            f"{statistics.median(gaps) if gaps else 0:5.0f} cp | p90 "
            f"{(gaps[int(0.9*len(gaps))-1] if len(gaps) > 1 else 0):5d} | move_mismatch {bmmis:3d}")
    out.append(line)
    print(line, flush=True)
text = "\n".join(out) + "\n"
with open(os.path.join(OUTDIR, "depthgap.txt"), "w") as fh:
    fh.write(text)
