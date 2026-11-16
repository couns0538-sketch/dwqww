#!/usr/bin/env python3
"""throughput_cost.py EXE OUTDIR : wall time per search at each self-play node budget.

Prices the S-F32 recommendation. 10 reps per budget on one position, fresh process per search, monotonic clock
from the moment `go nodes B` is written to the moment `bestmove` is read. PC build under PC20, Threads 1, Hash 16.
"""
import os
import re
import statistics
import subprocess
import sys
import time

EXE, OUTDIR = sys.argv[1], sys.argv[2]
os.makedirs(OUTDIR, exist_ok=True)
REPS = 10
BUDGETS = [2000, 8000, 20000, 50000, 250000]
FEN = "1r6/2k2pp1/2p2n2/2Pppb1p/7P/1P2PPP1/P3BK2/R1R5 b - - 0 1"

S14 = {"LmrQuietBase": 93, "LmrQuietDivisor": 205, "LmrNoisyBase": 13, "LmrNoisyDivisor": 333,
       "LmrHistoryDivisor": 5643, "NullMoveBase": 5, "LmpBase": 8, "HistoryPruneMultiplier": 2220,
       "HistoryBonusQuadratic": 24, "HistoryBonusLinear": 54, "HistoryBonusMax": 2212,
       "SingularDepth": 6, "IirDepth": 2, "NonPawnCorrection": "true"}
PC20 = {**S14, "CuckooRep": "true", "HistRework": 2, "TtPruneV2": "true", "CorrHistV2": "true",
        "MateAlphaGuard": "true", "OwnBook": "false", "Threads": 1, "Hash": 16}


class Missing(Exception):
    pass


def timed(fen, gov):
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)

    def send(c):
        p.stdin.write(c + "\n")
        p.stdin.flush()

    def to(tok, lim=400):
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
    send(gov)
    lines, ok = to("bestmove", 400)
    wall = (time.monotonic() - t0) * 1000.0
    send("quit")
    try:
        p.wait(timeout=10)
    except Exception:
        p.kill()
    if not ok:
        raise Missing(f"no bestmove for {gov}")
    eng = None
    for l in lines:
        m = re.search(r"\btime (\d+)", l)
        if l.startswith("info") and m:
            eng = int(m.group(1))
    return wall, eng


out = [f"exe {EXE}", f"position {FEN}", "PC20 + Threads 1 + Hash 16, fresh process per search, "
       "monotonic clock from `go` to `bestmove`", f"reps {REPS}", "",
       "budget | wall median | wall p99 | wall max | engine-reported median | searches/sec"]
print(out[-1])
base = None
summary = {}
for B in BUDGETS:
    walls = []
    engs = []
    try:
        for _ in range(REPS):
            w, e = timed(FEN, f"go nodes {B}")
            walls.append(w)
            if e is not None:
                engs.append(e)
    except Missing as exc:
        out.append(f"{B:6d} | NOT MEASURED: {exc}")
        print(out[-1])
        continue
    walls.sort()
    med = statistics.median(walls)
    p99 = walls[int(0.99 * len(walls)) - 1]
    sps = 1000.0 / med if med > 0 else 0
    if base is None:
        base = med
    line = (f"{B:6d} | {med:9.1f} ms | {p99:7.1f} | {max(walls):7.1f} | "
            f"{(statistics.median(engs) if engs else 0):9.0f} ms | {sps:6.1f}  "
            f"(x{med/base:.1f} vs 2000)")
    out.append(line)
    summary[B] = med
    print(line, flush=True)

if 2000 in summary and 20000 in summary:
    out.append("")
    out.append(f"cost of the recommendation: move time x{summary[20000]/summary[2000]:.1f}, "
               f"throughput /{(summary[20000]/summary[2000]):.1f}")
text = "\n".join(out) + "\n"
print(out[-1])
with open(os.path.join(OUTDIR, "throughput_cost.txt"), "w") as fh:
    fh.write(text)
