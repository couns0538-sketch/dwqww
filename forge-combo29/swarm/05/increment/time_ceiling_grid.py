#!/usr/bin/env python3
"""time_ceiling_grid.py EXE -- where is the ABSOLUTE ceiling on time per move?

S-F53/S-F54 showed that above an increment of ~6000 ms the time spent stops growing (with the clock fixed at 6000 ms).
That leaves two possibilities, and they imply different advice for the owner:
  (a) the ceiling is proportional to the CLOCK  -> raising the clock raises the ceiling, so the owner's lever is the clock
  (b) the ceiling is ABSOLUTE                   -> no control raises it, and there is a hard cap per move

Method: a grid of (clock, increment) pairs, all at PC20 / Threads 1 / Hash 16 / OwnBook false, sequential, on the
same positions. Report median and max wall time plus median depth for each cell, and the max seen anywhere.

Cells are chosen to separate the two hypotheses:
  clock 6000  x inc {60, 6000, 24000}   (the known flat region)
  clock 20000 x inc {60, 6000, 24000}   (a bigger clock: does the flat region rise?)
  clock 60000 x inc {6000, 24000}       (a much bigger clock)
"""
import re
import subprocess
import sys
import time

EXE = sys.argv[1] if len(sys.argv) > 1 else "/tmp/build-pc/forge"
RUNS = int(sys.argv[2]) if len(sys.argv) > 2 else 3
NPOS = int(sys.argv[3]) if len(sys.argv) > 3 else 4

OPTS = ["setoption name Threads value 1", "setoption name Hash value 16",
        "setoption name OwnBook value false",
        "setoption name LmrQuietBase value 93", "setoption name LmrQuietDivisor value 205",
        "setoption name LmrNoisyBase value 13", "setoption name LmrNoisyDivisor value 333",
        "setoption name LmrHistoryDivisor value 5643", "setoption name NullMoveBase value 5",
        "setoption name LmpBase value 8", "setoption name HistoryPruneMultiplier value 2220",
        "setoption name HistoryBonusQuadratic value 24", "setoption name HistoryBonusLinear value 54",
        "setoption name HistoryBonusMax value 2212", "setoption name SingularDepth value 6",
        "setoption name IirDepth value 2", "setoption name NonPawnCorrection value true",
        "setoption name CuckooRep value true", "setoption name HistRework value 2",
        "setoption name TtPruneV2 value true", "setoption name CorrHistV2 value true",
        "setoption name MateAlphaGuard value true"]
BAD = ("unknown option", "invalid value", "invalid FEN", "illegal move")

# (clock ms, increment ms)
CELLS = [(6000, 60), (6000, 6000), (6000, 24000),
         (20000, 60), (20000, 6000), (20000, 24000),
         (60000, 6000), (60000, 24000)]


def run(fen, clock, inc):
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    L = []

    def s(x):
        p.stdin.write(x + "\n")
        p.stdin.flush()

    def u(t, lim=400):
        t0 = time.time()
        while time.time() - t0 < lim:
            l = p.stdout.readline()
            if l == "":
                return False
            l = l.rstrip()
            L.append(l)
            if any(b in l for b in BAD):
                return False
            if l.startswith(t):
                return True
        return False

    s("uci")
    if not u("uciok"):
        p.kill()
        return None
    for o in OPTS:
        s(o)
        s("isready")
        if not u("readyok"):
            p.kill()
            return None
    s("ucinewgame"); s("isready"); u("readyok")
    s(f"position fen {fen}"); s("isready"); u("readyok")
    t0 = time.monotonic()
    s(f"go wtime {clock} btime {clock} winc {inc} binc {inc}")
    ok = u("bestmove")
    wall = time.monotonic() - t0
    s("quit")
    try:
        p.wait(timeout=30)
    except Exception:
        p.kill()
    if not ok:
        return None
    pv = [x for x in L if re.search(r"\binfo\b.*\bpv\b", x)]
    if not pv:
        return None
    last = pv[-1]
    d = re.search(r"depth (\d+)", last)
    et = re.search(r"\btime (\d+)", last)
    return dict(wall=wall, depth=int(d.group(1)) if d else None,
                etime=int(et.group(1)) if et else None)


def pct(vals, p):
    s = sorted(v for v in vals if v is not None)
    if not s:
        return None
    if len(s) == 1:
        return s[0]
    k = (len(s) - 1) * p / 100.0
    f = int(k)
    c = min(f + 1, len(s) - 1)
    return s[f] + (s[c] - s[f]) * (k - f) if f != c else s[f]


allg = [l.split(";")[0].strip() for l in open("../job1/data/G.epd") if l.strip()]
step = max(1, len(allg) // NPOS)
FENS = [allg[i] for i in range(0, len(allg), step)][:NPOS]

print(f"exe: {EXE}   PC20, Threads 1, Hash 16, OwnBook false   SEQUENTIAL")
print(f"{NPOS} G positions x {RUNS} runs per cell   date_utc: {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}")
print()
print("| clock (ms) | increment (ms) | n | median wall (ms) | max wall (ms) | median engine time (ms) | median depth | max depth |")
print("|---|---|---|---|---|---|---|---|")
global_max = 0
global_max_cell = None
for clock, inc in CELLS:
    res = []
    for fen in FENS:
        for _ in range(RUNS):
            r = run(fen, clock, inc)
            if r:
                res.append(r)
    if not res:
        print(f"| {clock} | {inc} | 0 | NO MEASUREMENT | - | - | - | - |")
        continue
    walls = [r["wall"] * 1000 for r in res]
    etimes = [r["etime"] for r in res]
    depths = [r["depth"] for r in res if r["depth"]]
    mx = max(walls)
    if mx > global_max:
        global_max = mx
        global_max_cell = (clock, inc)
    print(f"| {clock} | {inc} | {len(res)} | {pct(walls,50):.0f} | {mx:.0f} | "
          f"{pct(etimes,50) if etimes[0] is not None else 0:.0f} | "
          f"{pct(depths,50) if depths else 0:.0f} | {max(depths) if depths else 0} |")

print()
print(f"largest wall time seen anywhere in the grid: {global_max:.0f} ms at clock/increment {global_max_cell}")
print()
print("Reading: compare the inc 6000 and inc 24000 rows INSIDE each clock block. If they are equal at clock 6000 but")
print("differ at clock 20000/60000, the ceiling scales with the clock (hypothesis a). If they are equal everywhere,")
print("the ceiling is absolute (hypothesis b).")
