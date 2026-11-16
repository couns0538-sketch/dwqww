#!/usr/bin/env python3
"""sf6_recheck.py — re-measure S-F6 with the plan AND the achieved time for both sides, plus depth.

S-F6 said: `wtime 1600 winc 1000` (a GUI gives 2600 ms) searches median 604 ms while `wtime 2600
winc 0` (the same 2600 ms) searches median 92 ms. Both are ACHIEVED times, so the ratio is like-for-like
and iteration granularity cannot manufacture the direction — but it can inflate the magnitude on the
fast side. This run measures both sides at three total clocks with everything else fixed, and records
the last completed depth per search so the reader can see how much the fast side is one iteration short.

Cells: total 1200, 1800, 2600 with (wtime = total-1000, winc = 1000) vs (wtime = total, winc = 0).
24 positions per cell, OwnBook false, Threads 1, Hash 16.

Usage: sf6_recheck.py EXE OUTDIR
"""
import os
import statistics
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "job1"))
from timing import Engine, read_positions  # noqa: E402

TOTALS = (1200, 1800, 2600)
NPOS = 24
OVERHEAD = 10
SOFT_DIV = 22
INC_PCT = 75
HARD_PCT = 60
HARD_MULT = 5


def plan(time_ms, inc_ms):
    """Verbatim port of include/forge/clock_plan.hpp plan_clock_budget for moves_to_go = 0.

    The clamp `if (soft > hard) soft = hard` on line 47 is PART of the plan: with a big increment and
    a small clock, soft is computed first and can exceed hard, and the engine then lowers soft to hard.
    A first version of this function omitted that clamp and printed soft 190 / hard 114 for
    `wtime 200 winc 1000`, i.e. soft above hard, which the engine never plans. Fixed here.
    """
    if time_ms <= OVERHEAD:
        return 0, 0
    avail = time_ms - OVERHEAD
    soft = avail // SOFT_DIV + inc_ms * INC_PCT // 100
    hard = min(avail * HARD_PCT // 100, soft * HARD_MULT)
    soft = max(1, min(soft, avail))
    hard = max(1, min(hard, avail))
    if soft > hard:
        soft = hard
    return soft, hard


def cell(exe, fens, wtime, winc):
    eng = Engine(exe)
    eng.send("uci")
    eng.read_until("uciok", 20)
    for opt, val in [("OwnBook", "false"), ("Threads", 1), ("Hash", 16)]:
        eng.send(f"setoption name {opt} value {val}")
        eng.send("isready")
        eng.read_until("readyok", 20)
    walls, eng_t, depths = [], [], []
    for fen in fens:
        eng.send("ucinewgame")
        eng.send("isready")
        eng.read_until("readyok", 20)
        eng.send(f"position fen {fen}")
        eng.send("isready")
        eng.read_until("readyok", 20)
        t0 = time.monotonic()
        eng.send(f"go wtime {wtime} btime {wtime} winc {winc} binc {winc}")
        out, ok = eng.read_until("bestmove", 120)
        t1 = time.monotonic()
        if not ok:
            raise SystemExit(f"NORESP at wtime {wtime} winc {winc}")
        walls.append((t1 - t0) * 1000.0)
        et, d = None, 0
        for line in out:
            if line.startswith("info depth"):
                f = line.split()
                d = max(d, int(f[f.index("depth") + 1]))
                if "time" in f:
                    et = float(f[f.index("time") + 1])
        eng_t.append(et)
        depths.append(d)
    eng.close()
    return walls, [e for e in eng_t if e is not None], depths


def main() -> int:
    exe, outdir = sys.argv[1], sys.argv[2]
    os.makedirs(outdir, exist_ok=True)
    here = os.path.dirname(os.path.abspath(__file__))
    fens = read_positions([os.path.join(here, "..", "job1", "G.epd")], NPOS)
    fens = [f.split(";")[0].split(" bm")[0].strip() for f in fens]

    print("| total clock | side | wtime | winc | plan soft | plan hard | achieved median | last-info "
          "median | attained/plan | last depth (mode) |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    for total in TOTALS:
        for side, wtime, winc in (("A inc", total - 1000, 1000), ("B clock", total, 0)):
            soft, hard = plan(wtime, winc)
            walls, eng_t, depths = cell(exe, fens, wtime, winc)
            med = statistics.median(walls)
            em = statistics.median(eng_t) if eng_t else float("nan")
            mode = max(set(depths), key=depths.count)
            print(f"| {total} | {side} | {wtime} | {winc} | {soft} | {hard} | {med:.1f} | {em:.0f} | "
                  f"{med/soft:.2f} | d{mode} |")
            with open(os.path.join(outdir, f"total{total}_{side.split()[0]}.tsv"), "w") as fh:
                fh.write("fen\twall_ms\tengine_time_ms\tlast_depth\n")
                for f, w, e, d in zip(fens, walls, eng_t + [None] * len(fens), depths):
                    fh.write(f"{f}\t{w:.3f}\t{e if e is not None else ''}\t{d}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
