#!/usr/bin/env python3
"""Third independent measurement of the PC's real match clock, `6s + 0.06`, on the PC r15 build under PC20.

The two seats disagree about clock overrun behaviour (seat 08 measures 46 of 200 searches past the engine's own soft
limit at a 10 s clock; seat 06's depth-curve work implies boundary stopping). This run gives a large independent
sample on the regime the owner actually uses, and reports against BOTH the soft and hard limits computed from
`include/forge/clock_plan.hpp` so the comparison is explicit rather than assuming which limit the seats meant.

Per search, from a monotonic clock around `go` -> `bestmove`:
  wall ms, reported depth, nodes, and whether it exceeded soft / hard.
Threads 1, Hash 16, fresh process per search.
"""
import statistics
import subprocess
import sys
import time

EXE = sys.argv[1]
FENS = [l.strip() for l in open(sys.argv[2]) if l.strip()]
WTIME, WINC, OVERHEAD = 6000, 60, 10

S14 = [("LmrQuietBase", 93), ("LmrQuietDivisor", 205), ("LmrNoisyBase", 13), ("LmrNoisyDivisor", 333),
       ("LmrHistoryDivisor", 5643), ("NullMoveBase", 5), ("LmpBase", 8), ("HistoryPruneMultiplier", 2220),
       ("HistoryBonusQuadratic", 24), ("HistoryBonusLinear", 54), ("HistoryBonusMax", 2212),
       ("SingularDepth", 6), ("IirDepth", 2), ("NonPawnCorrection", "true")]
PC20 = S14 + [("CuckooRep", "true"), ("HistRework", 2), ("TtPruneV2", "true"), ("CorrHistV2", "true"),
              ("MateAlphaGuard", "true"), ("OwnBook", "false")]

# The same arithmetic as plan_clock_budget() for a sudden-death clock with default divisors (soft 5, inc 10 %,
# hard 80 %, multiple 4): soft = avail/5 + inc*10/100 ; hard = min(avail*80/100, soft*4).
available = max(0, WTIME - OVERHEAD)
SOFT = max(1, min(available // 5 + WINC * 10 // 100, available))
HARD = max(1, min(min(available * 80 // 100, SOFT * 4), available))
print(f"clock wtime {WTIME} btime {WTIME} winc {WINC} binc {WINC}; computed soft {SOFT} ms, hard {HARD} ms")
print(f"{len(FENS)} positions, Threads 1, Hash 16, PC20, PC r15 build")
print()


def one(fen):
    p = subprocess.Popen([EXE], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)

    def send(s):
        p.stdin.write(s + "\n")
        p.stdin.flush()

    send("uci")
    for line in p.stdout:
        if line.startswith("uciok"):
            break
    send("setoption name Hash value 16")
    send("setoption name Threads value 1")
    for k, v in PC20:
        send(f"setoption name {k} value {v}")
    send("isready")
    for line in p.stdout:
        if line.startswith("readyok"):
            break
    send(f"position fen {fen}")
    t0 = time.monotonic()
    send(f"go wtime {WTIME} btime {WTIME} winc {WINC} binc {WINC}")
    last = None
    bm = None
    for line in p.stdout:
        if line.startswith("info depth"):
            last = line.rstrip()
        if line.startswith("bestmove"):
            bm = line.split()[1]
            break
    ms = (time.monotonic() - t0) * 1000.0
    send("quit")
    p.wait(timeout=180)
    if last is None or bm is None:
        raise SystemExit(f"ABORT: incomplete search for {fen}")
    f = last.split()
    return ms, int(f[2]), int(f[f.index("nodes") + 1]), bm


rows = []
for i, fen in enumerate(FENS, 1):
    ms, d, n, bm = one(fen)
    rows.append((i, ms, d, n, bm))
    print(f"pos {i:>2}: {ms:7.1f} ms  depth {d:>2}  nodes {n:>7}  {bm}")

times = sorted(r[1] for r in rows)
n = len(times)
print()
print("| statistic | value |")
print("|---|---|")
print(f"| searches | {n} |")
print(f"| min | {times[0]:.0f} ms |")
print(f"| median | {statistics.median(times):.0f} ms |")
print(f"| p99 | {times[max(0, int(0.99 * n) - 1)]:.0f} ms |")
print(f"| max | {times[-1]:.0f} ms |")
print(f"| past SOFT {SOFT} ms | {sum(1 for t in times if t > SOFT)} of {n} |")
print(f"| past HARD {HARD} ms | {sum(1 for t in times if t > HARD)} of {n} |")
print(f"| median as % of 6000 ms clock | {100 * statistics.median(times) / WTIME:.1f} % |")
