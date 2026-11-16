#!/usr/bin/env python3
"""increment_scaling.py EXE -- does the time manager SPEND more when the increment is raised 10x (0.06 -> 0.6 s)?

The question the owner needs answered: does raising `winc` actually buy thinking time, or does the time manager
plateau? Everything else fixed: 6000 ms clock, PC20, Threads 1, Hash 16, OwnBook false, the same 10 positions,
the same protocol.

Protocol: for each (position, increment) pair, RUNS fresh processes; wall time measured with a monotonic clock from
sending `go` to reading `bestmove`, engine's own `time` field recorded beside it, depth and nodes from the last pv
line. SEQUENTIAL ONLY — one engine process at a time, so no CPU contention (see ../MEASUREMENT_WARNING.txt).

Reported per increment: n, median, p90, max, and the median depth. Per position: median wall and depth for each
increment, so a reader can see whether the effect is uniform or driven by a few boards.
"""
import re
import subprocess
import sys
import time

EXE = sys.argv[1] if len(sys.argv) > 1 else "/tmp/build-pc/forge"
RUNS = int(sys.argv[2]) if len(sys.argv) > 2 else 5
NPOS = int(sys.argv[3]) if len(sys.argv) > 3 else 10

CLOCK = 6000
SMALL_INC = 60      # 0.06 s, the owner's strength-match increment
BIG_INC = 600       # 0.6 s, the deliberate 10x

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


def run(fen, winc):
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True, bufsize=1)
    L = []

    def s(x):
        p.stdin.write(x + "\n")
        p.stdin.flush()

    def u(t, lim=300):
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
    s("ucinewgame")
    s("isready")
    u("readyok")
    s(f"position fen {fen}")
    s("isready")
    u("readyok")
    t0 = time.monotonic()
    s(f"go wtime {CLOCK} btime {CLOCK} winc {winc} binc {winc}")
    ok = u("bestmove")
    wall = time.monotonic() - t0
    s("quit")
    try:
        p.wait(timeout=20)
    except Exception:
        p.kill()
    if not ok:
        return None                     # no bestmove => no measurement, never a zero
    pv = [x for x in L if re.search(r"\binfo\b.*\bpv\b", x)]
    if not pv:
        return None                     # no pv => not measured (the OwnBook trap)
    last = pv[-1]
    d = re.search(r"depth (\d+)", last)
    n = re.search(r"\bnodes (\d+)", last)
    et = re.search(r"\btime (\d+)", last)
    return dict(wall=wall, depth=int(d.group(1)) if d else None,
                nodes=int(n.group(1)) if n else None,
                etime=int(et.group(1)) if et else None)


def pct(vals, p):
    """nearest-rank percentile, stated so a reader can reproduce it"""
    s = sorted(vals)
    if not s:
        return None
    if len(s) == 1:
        return s[0]
    k = (len(s) - 1) * p / 100.0
    f = int(k)
    c = min(f + 1, len(s) - 1)
    return s[f] + (s[c] - s[f]) * (k - f) if f != c else s[f]


# 10 positions spread across the G set (positions taken from real games), not the first 10 in a row
allg = [l.split(";")[0].strip() for l in open("../job1/data/G.epd") if l.strip()]
step = max(1, len(allg) // NPOS)
FENS = [allg[i] for i in range(0, len(allg), step)][:NPOS]

print(f"exe: {EXE}   clock {CLOCK} ms   increments {SMALL_INC} vs {BIG_INC} ms   {RUNS} runs each")
print(f"PC20, Threads 1, Hash 16, OwnBook false, SEQUENTIAL (one engine at a time)")
print(f"positions: {len(FENS)} from G.epd (real games)   date_utc: "
      f"{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}")
print()

data = {SMALL_INC: {}, BIG_INC: {}}
for i, fen in enumerate(FENS):
    for inc in (SMALL_INC, BIG_INC):
        res = []
        for _ in range(RUNS):
            r = run(fen, inc)
            if r is None:
                print(f"!! pos {i} inc {inc}: a run produced no measurement (refused or no pv) — cell void")
            else:
                res.append(r)
        data[inc][i] = res
    sm = [r["wall"] * 1000 for r in data[SMALL_INC][i]]
    bg = [r["wall"] * 1000 for r in data[BIG_INC][i]]
    smd = [r["depth"] for r in data[SMALL_INC][i] if r["depth"]]
    bgd = [r["depth"] for r in data[BIG_INC][i] if r["depth"]]
    print(f"pos {i:2d}  inc {SMALL_INC}: median {pct(sm,50):6.0f} ms  depth {pct(smd,50) if smd else '-'}   |   "
          f"inc {BIG_INC}: median {pct(bg,50):6.0f} ms  depth {pct(bgd,50) if bgd else '-'}")

print()
print("=" * 92)
print("AGGREGATE over all runs")
print()
print("| increment | n | median (ms) | p90 (ms) | max (ms) | median depth | max depth | median engine time (ms) | median nodes |")
print("|---|---|---|---|---|---|---|---|---|")
for inc in (SMALL_INC, BIG_INC):
    walls, depths, etimes, nodes = [], [], [], []
    for i in range(len(FENS)):
        for r in data[inc][i]:
            walls.append(r["wall"] * 1000)
            if r["depth"]:
                depths.append(r["depth"])
            if r["etime"] is not None:
                etimes.append(r["etime"])
            if r["nodes"]:
                nodes.append(r["nodes"])
    print(f"| {inc} | {len(walls)} | {pct(walls,50):.0f} | {pct(walls,90):.0f} | {max(walls):.0f} | "
          f"{pct(depths,50):.0f} | {max(depths)} | {pct(etimes,50):.0f} | {pct(nodes,50):.0f} |")

print()
sw = [r["wall"] * 1000 for i in range(len(FENS)) for r in data[SMALL_INC][i]]
bw = [r["wall"] * 1000 for i in range(len(FENS)) for r in data[BIG_INC][i]]
sd = [r["depth"] for i in range(len(FENS)) for r in data[SMALL_INC][i] if r["depth"]]
bd = [r["depth"] for i in range(len(FENS)) for r in data[BIG_INC][i] if r["depth"]]
if sw and bw:
    ratio = pct(bw, 50) / pct(sw, 50) if pct(sw, 50) else 0
    print(f"median wall: {pct(sw,50):.0f} -> {pct(bw,50):.0f} ms  = {ratio:.2f}x for a 10x increment")
    print(f"median depth: {pct(sd,50):.0f} -> {pct(bd,50):.0f}  = {(pct(bd,50)-pct(sd,50)):+.0f} plies")
    print()
    print("Reading: if the median wall time scales with the increment (ratio well above 1 and depth rising),")
    print("raising the increment DOES buy thinking time. If the median barely moves, the time manager plateaus")
    print("and a bigger increment buys nothing on this path.")
