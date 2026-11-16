#!/usr/bin/env python3
"""depth_onset.py EXE OUTDIR : at which depth does each asymmetry begin, on the full G set?

Depths 1 and 2, all 353 G positions and their colour mirrors, PC build under PC20, Threads 1, Hash 16, cold
(fresh process + ucinewgame per search). Reports score-equal, bestmove-equal and node-equal counts per depth,
so the depth of onset is established separately for each quantity.
"""
import os
import re
import subprocess
import sys
import time

import chess

EXE, OUTDIR = sys.argv[1], sys.argv[2]
os.makedirs(OUTDIR, exist_ok=True)
DEPTHS = [1, 2]

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

    def to(tok, lim=240):
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
    lines, ok = to("bestmove", 240)
    send("quit")
    try:
        p.wait(timeout=10)
    except Exception:
        p.kill()
    if not ok:
        raise Missing("no bestmove")
    best = score = nodes = None
    for l in lines:
        if l.startswith("bestmove"):
            best = l.split()[1]
        m = re.search(rf"^info depth {depth} .*score (cp|mate) (-?\d+) nodes (\d+)", l)
        if m:
            score = (m.group(1), int(m.group(2)))
            nodes = int(m.group(3))
    if best is None or score is None or nodes is None:
        raise Missing(f"incomplete at depth {depth}")
    return best, score, nodes


def back(mv):
    if not mv or mv == "0000":
        return None
    m = chess.Move.from_uci(mv)
    return chess.Move(m.from_square ^ 56, m.to_square ^ 56, m.promotion).uci()


fens = [l.strip() for l in open("/agent/repos/dwqww/forge-combo29/swarm/16/depth_onset/set_G.epd")
        if l.strip()]
out = [f"exe {EXE}", f"positions {len(fens)}", "PC20 + Threads 1 + Hash 16, cold per search", "",
       "depth | score equal | bestmove equal | node equal | of"]
print(out[-1])
for depth in DEPTHS:
    se = be = ne = n = 0
    for fen in fens:
        mir = chess.Board(fen).mirror().fen()
        try:
            ba, sa, na = search(fen, depth)
            bb, sb, nb = search(mir, depth)
        except Missing:
            continue
        n += 1
        se += (sa == sb)
        be += (ba == back(bb))
        ne += (na == nb)
    line = f"{depth:5d} | {se:5d} | {be:5d} | {ne:5d} | {n:3d}"
    out.append(line)
    print(line, flush=True)

text = "\n".join(out) + "\n"
with open(os.path.join(OUTDIR, "depth_onset.txt"), "w") as fh:
    fh.write(text)
