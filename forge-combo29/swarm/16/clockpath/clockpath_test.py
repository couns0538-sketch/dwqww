#!/usr/bin/env python3
"""clockpath_test.py EXE OUTDIR : the PC's match path under PC20, Threads 1.

`go wtime 6000 btime 6000 winc 60 binc 60` — 20 runs per position on 4 positions from real games.
Records wall time (monotonic, go -> bestmove), the engine's own reported time, depth, score, nodes, bestmove.
Reports determinism of the move, the spread of score/nodes, and any run that exceeded the clock.
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
REPS = 20
WT, BT, WI, BI = 6000, 6000, 60, 60

S14 = {"LmrQuietBase": 93, "LmrQuietDivisor": 205, "LmrNoisyBase": 13, "LmrNoisyDivisor": 333,
       "LmrHistoryDivisor": 5643, "NullMoveBase": 5, "LmpBase": 8, "HistoryPruneMultiplier": 2220,
       "HistoryBonusQuadratic": 24, "HistoryBonusLinear": 54, "HistoryBonusMax": 2212,
       "SingularDepth": 6, "IirDepth": 2, "NonPawnCorrection": "true"}
PC20 = {**S14, "CuckooRep": "true", "HistRework": 2, "TtPruneV2": "true", "CorrHistV2": "true",
        "MateAlphaGuard": "true", "OwnBook": "false", "Threads": 1, "Hash": 16}

POSITIONS = [
    ("G0", "1r6/2k2pp1/2p2n2/2Pppb1p/7P/1P2PPP1/P3BK2/R1R5 b - - 0 1"),
    ("G1", "r3r1k1/p1bb1ppp/1p1q4/3P1p2/1nBP4/PPN2N1P/5PP1/1R1Q1RK1 b - - 0 1"),
    ("G6", "2r4r/pp4k1/3q2p1/3ppn2/1P4QP/P2P1N2/R4P2/4RK2 b - - 0 1"),
    ("G10", "4r1k1/2pn1pp1/1p5p/p3p3/PP2P3/2PB2P1/5P1P/R5K1 b - - 0 1"),
]


class Missing(Exception):
    pass


def go_clock(fen):
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)

    def send(c):
        p.stdin.write(c + "\n")
        p.stdin.flush()

    def to(tok, lim=60):
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
    t0 = time.monotonic()
    send(f"go wtime {WT} btime {BT} winc {WI} binc {BI}")
    lines, ok = to("bestmove", 60)
    wall = (time.monotonic() - t0) * 1000.0
    send("quit")
    try:
        p.wait(timeout=10)
    except Exception:
        p.kill()
    if not ok:
        raise Missing("no bestmove within 60 s -> HANG")
    best = None
    last = None
    for l in lines:
        if l.startswith("bestmove"):
            best = l.split()[1]
        m = re.match(r"^info depth (\d+) .*score (cp|mate) (-?\d+) nodes (\d+).*? time (\d+).*?(?: pv (.*))?$", l)
        if m:
            last = (int(m.group(1)), f"{m.group(2)} {m.group(3)}", int(m.group(4)),
                    int(m.group(5)), (m.group(6) or "").split())
    if best is None or last is None:
        raise Missing("missing bestmove or info depth")
    return {"best": best, "depth": last[0], "score": last[1], "nodes": last[2],
            "eng_time": last[3], "wall": wall, "pv": last[4]}


out = [f"exe {EXE}", f"PC20 + Threads 1 + Hash 16; go wtime {WT} btime {BT} winc {WI} binc {BI}; {REPS} reps",
       "clock = 6.00 s + 0.06 s increment (the PC's match path)", ""]
for label, fen in POSITIONS:
    try:
        rs = [go_clock(fen) for _ in range(REPS)]
    except Missing as exc:
        out.append(f"### {label}: NOT MEASURED: {exc}")
        print(out[-1], flush=True)
        continue
    bests = {r["best"] for r in rs}
    scores = {r["score"] for r in rs}
    depths = sorted({r["depth"] for r in rs})
    nodes = [r["nodes"] for r in rs]
    walls = [r["wall"] for r in rs]
    overs = [w for w in walls if w > WT + WI]
    in_pv = sum(1 for r in rs if r["best"] in r["pv"])
    block = [
        f"### {label}  {fen}",
        f"  distinct bestmoves {len(bests)}: {sorted(bests)}",
        f"  distinct scores {len(scores)}: {sorted(scores)}",
        f"  depths reached {depths}",
        f"  nodes  min {min(nodes)} median {statistics.median(nodes):.0f} max {max(nodes)}",
        f"  wall   min {min(walls):.1f} median {statistics.median(walls):.1f} max {max(walls):.1f} ms  "
        f"(over {WT+WI} ms: {len(overs)} of {len(rs)})",
        f"  bestmove present in its own PV: {in_pv}/{len(rs)}",
    ]
    out.append("\n".join(block))
    print(out[-1], flush=True)
    out.append("")

text = "\n".join(out) + "\n"
with open(os.path.join(OUTDIR, "clockpath.txt"), "w") as fh:
    fh.write(text)
