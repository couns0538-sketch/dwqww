#!/usr/bin/env python3
"""clock_scale.py EXE OUTDIR : does the fraction of the clock the engine USES change with the clock size?

If the engine always uses ~3-5% regardless of the clock, it is depth-bounded on this hardware (the search
finishes a depth and stops). If the fraction GROWS with a smaller clock, the time manager is the binding limit
there and the 5% at 6 s is a soft-limit choice, not a hardware ceiling.

Clocks tested on one real-game position, PC20 + Threads 1 + Hash 16, 5 reps each:
  wtime/btime 1000/1000 winc 10      (1 s)
  wtime/btime 3000/3000 winc 30      (3 s)
  wtime/btime 6000/6000 winc 60      (6 s, the PC's match path)
  wtime/btime 30000/30000 winc 300   (30 s)
Records wall time, reported engine time, depth, nodes, bestmove.
"""
import os
import re
import statistics
import subprocess
import sys
import time

EXE, OUTDIR = sys.argv[1], sys.argv[2]
os.makedirs(OUTDIR, exist_ok=True)
REPS = 5
FEN = "1r6/2k2pp1/2p2n2/2Pppb1p/7P/1P2PPP1/P3BK2/R1R5 b - - 0 1"
CLOCKS = [(1000, 10), (3000, 30), (6000, 60), (30000, 300)]

S14 = {"LmrQuietBase": 93, "LmrQuietDivisor": 205, "LmrNoisyBase": 13, "LmrNoisyDivisor": 333,
       "LmrHistoryDivisor": 5643, "NullMoveBase": 5, "LmpBase": 8, "HistoryPruneMultiplier": 2220,
       "HistoryBonusQuadratic": 24, "HistoryBonusLinear": 54, "HistoryBonusMax": 2212,
       "SingularDepth": 6, "IirDepth": 2, "NonPawnCorrection": "true"}
PC20 = {**S14, "CuckooRep": "true", "HistRework": 2, "TtPruneV2": "true", "CorrHistV2": "true",
        "MateAlphaGuard": "true", "OwnBook": "false", "Threads": 1, "Hash": 16}


class Missing(Exception):
    pass


def go_clock(t, inc, limit_s):
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)

    def send(c):
        p.stdin.write(c + "\n")
        p.stdin.flush()

    def to(tok, lim=limit_s + 15):
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
    send("position fen " + FEN); send("isready"); to("readyok", 20)
    t0 = time.monotonic()
    send(f"go wtime {t} btime {t} winc {inc} binc {inc}")
    lines, ok = to("bestmove", limit_s + 15)
    wall = (time.monotonic() - t0) * 1000.0
    send("quit")
    try:
        p.wait(timeout=10)
    except Exception:
        p.kill()
    if not ok:
        raise Missing("no bestmove")
    best = None
    last = None
    for l in lines:
        if l.startswith("bestmove"):
            best = l.split()[1]
        m = re.match(r"^info depth (\d+) .*score (cp|mate) (-?\d+) nodes (\d+).*? time (\d+)", l)
        if m:
            last = (int(m.group(1)), int(m.group(4)), int(m.group(5)))
    if best is None or last is None:
        raise Missing("missing bestmove or depth line")
    return {"best": best, "depth": last[0], "nodes": last[1], "eng_ms": last[2], "wall": wall}


out = [f"exe {EXE}", f"position {FEN}", "PC20 + Threads 1 + Hash 16", f"reps per clock: {REPS}", ""]
allowed_total = 0
for t, inc in CLOCKS:
    allowed = t + inc
    try:
        rs = [go_clock(t, inc, allowed / 1000.0) for _ in range(REPS)]
    except Missing as exc:
        out.append(f"clock {t:6d}+{inc:<4d}: NOT MEASURED: {exc}")
        print(out[-1], flush=True)
        continue
    eng = [r["eng_ms"] for r in rs]
    walls = [r["wall"] for r in rs]
    depths = sorted({r["depth"] for r in rs})
    bests = {r["best"] for r in rs}
    pct = [100.0 * e / allowed for e in eng]
    over = sum(1 for w in walls if w > allowed)
    line = (f"clock {t:6d}+{inc:<4d} allowed {allowed:6d} ms | engine time median {statistics.median(eng):8.1f} ms "
            f"({statistics.median(pct):5.2f} % of allowed) | depths {depths} | distinct bestmoves {len(bests)} | "
            f"over-clock {over}/{len(rs)}")
    out.append(line)
    print(line, flush=True)

text = "\n".join(out) + "\n"
with open(os.path.join(OUTDIR, "clock_scale.txt"), "w") as fh:
    fh.write(text)
