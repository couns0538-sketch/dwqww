#!/usr/bin/env python3
"""overshoot_one_iteration.py RAWDIR — the GUI author's number for 08-F11.

For each clock size, for every search, I need (a) the wall time, (b) the planned soft limit, (c) the cost of one
iteration near the stop. (c) is not in the timing files, so I measure it directly here: for each clock size, run
the searches and record every `info depth` line with its elapsed time, so the cost of the last completed
iteration is known per search.

Then report, per clock size:
  - fraction of searches exceeding PLAN SOFT at all
  - fraction exceeding soft by more than ONE WHOLE ITERATION (i.e. overrun > cost of the last iteration)
  - the worst absolute overshoot in ms
"""
import json
import subprocess
import sys
import time

exe, outpath = sys.argv[1:3]
FENS = [l.strip() for l in open("../job1/OG200.fens") if l.strip()]
CLOCKS = [200, 1000]
SOFT_DIV, OVERHEAD = 22, 10


def plan_soft(t):
    if t <= OVERHEAD:
        return 0
    return max(1, (t - OVERHEAD) // SOFT_DIV)


def run(fen, clock):
    before = ("uci\nsetoption name Threads value 1\nsetoption name Hash value 16\n"
              "setoption name OwnBook value false\nisready\nucinewgame\nisready\n"
              "position fen %s\nisready\n" % fen)
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.DEVNULL, text=True, bufsize=1)
    p.stdin.write(before)
    p.stdin.flush()
    while True:
        if p.stdout.readline().startswith("readyok"):
            break
    t0 = time.monotonic()
    p.stdin.write("go wtime %d btime %d\n" % (clock, clock))
    p.stdin.flush()
    marks = []
    while True:
        l = p.stdout.readline()
        if not l:
            raise EOFError
        ms = (time.monotonic() - t0) * 1000.0
        if l.startswith("info depth"):
            marks.append(ms)
        if l.startswith("bestmove"):
            wall = (time.monotonic() - t0) * 1000.0
            break
    p.stdin.write("quit\n")
    p.stdin.flush()
    try:
        p.wait(timeout=5)
    except Exception:
        p.kill()
    last_iter_cost = (marks[-1] - marks[-2]) if len(marks) >= 2 else marks[-1] if marks else 0.0
    return wall, last_iter_cost, len(marks)


rows = []
with open(outpath, "w") as out:
    out.write("clock\tfen\twall_ms\tsoft_ms\tlast_iter_cost_ms\tover_soft_ms\tover_by_more_than_one_iteration\n")
    for clock in CLOCKS:
        for fen in FENS:
            wall, cost, n = run(fen, clock)
            soft = plan_soft(clock)
            over = wall - soft
            more = over > cost
            rows.append({"clock": clock, "wall": wall, "soft": soft, "cost": cost, "over": over, "more": more})
            out.write("%d\t%s\t%.2f\t%d\t%.2f\t%.2f\t%d\n" % (clock, fen, wall, soft, cost, over, int(more)))
            out.flush()

print("## 08-F11 — the failure number: how far past the planned soft time does a search actually run?")
print()
print("| clock ms | searches | soft plan | median overshoot | worst overshoot ms | % over soft | % over soft by MORE than one whole iteration |")
print("|---|---|---|---|---|---|---|")
for clock in CLOCKS:
    sub = [r for r in rows if r["clock"] == clock]
    overs = sorted(r["over"] for r in sub)
    n = len(sub)
    print("| %d | %d | %d | %+.1f | **%+.1f** | %.0f %% | **%.0f %%** |" % (
        clock, n, sub[0]["soft"], overs[n // 2], max(overs),
        100.0 * sum(1 for r in sub if r["over"] > 0) / n,
        100.0 * sum(1 for r in sub if r["more"]) / n))
print()
print("## the worst few at each clock, with the iteration cost that explains them")
print("| clock | wall ms | soft | overshoot | cost of last iteration | overshoot / that cost |")
print("|---|---|---|---|---|---|")
for clock in CLOCKS:
    sub = sorted([r for r in rows if r["clock"] == clock], key=lambda r: -r["over"])[:3]
    for r in sub:
        ratio = (r["over"] / r["cost"]) if r["cost"] > 0 else float("nan")
        print("| %d | %.1f | %d | %+.1f | %.1f | %.2f |" % (clock, r["wall"], r["soft"], r["over"], r["cost"], ratio))
