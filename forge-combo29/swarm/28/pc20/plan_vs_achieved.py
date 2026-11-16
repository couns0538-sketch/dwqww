#!/usr/bin/env python3
"""plan_vs_achieved.py — the plan is identical on both builds; what differs is the stop.

The plan inputs were read from each exe's own `uci` answer (not from source): Move Overhead 10,
TmSoftDivisor 22, TmIncrementPercent 75, TmHardPercent 60, TmHardSoftMultiple 5 — IDENTICAL on base and
PC r15. So the plan at a given clock is the same number on both builds, computed here exactly as
include/forge/clock_plan.hpp does for moves_to_go = 0:

    available = time - overhead
    soft = available / soft_divisor + increment * increment_percent / 100
    hard = min(available * hard_percent / 100, soft * hard_soft_multiple)
    both clamped into 1..available; soft lowered to hard if soft > hard

This script then measures, per cell and per build, the ACHIEVED wall time and the time of the LAST
COMPLETED ITERATION (the engine's own `time` on its last `info depth` line), and reports achieved/soft
for both builds. If the plans are equal and achieved/soft differs, the difference is in the CHECK that
decides when to stop — not in the arithmetic.

It also prints, per build, the median depth and the median time of the last completed iteration, so the
10 s lost ply can be read directly.

Usage: plan_vs_achieved.py BASE_EXE PC_EXE OUTDIR [NPOS]
"""
import os
import statistics
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "job1"))
from timing import Engine, read_positions  # noqa: E402

S14 = {
    "LmrQuietBase": 93, "LmrQuietDivisor": 205, "LmrNoisyBase": 13, "LmrNoisyDivisor": 333,
    "LmrHistoryDivisor": 5643, "NullMoveBase": 5, "LmpBase": 8, "HistoryPruneMultiplier": 2220,
    "HistoryBonusQuadratic": 24, "HistoryBonusLinear": 54, "HistoryBonusMax": 2212,
    "SingularDepth": 6, "IirDepth": 2, "NonPawnCorrection": "true",
}
PC20_EXTRA = [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
              ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]
OVERHEAD, SOFT_DIV, INC_PCT, HARD_PCT, HARD_MULT = 10, 22, 75, 60, 5
CLOCKS = (3000, 10000)


def plan(time_ms, inc_ms=0):
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


def cell(exe, fens, wtime, pc20):
    eng = Engine(exe)
    eng.send("uci")
    eng.read_until("uciok", 20)
    sent = [("Threads", 1), ("Hash", 16)] + list(S14.items())
    sent += PC20_EXTRA if pc20 else [("OwnBook", "false")]
    for opt, val in sent:
        eng.send(f"setoption name {opt} value {val}")
        eng.send("isready")
        lines, ok = eng.read_until("readyok", 20)
        bad = [l for l in lines if "unknown option" in l or "invalid value" in l]
        if bad or not ok:
            raise SystemExit(f"STOP {opt}: {bad or 'no readyok'}")
    rows = []
    for fen in fens:
        eng.send("ucinewgame")
        eng.send("isready")
        eng.read_until("readyok", 20)
        eng.send(f"position fen {fen}")
        eng.send("isready")
        eng.read_until("readyok", 20)
        t0 = time.monotonic()
        eng.send(f"go wtime {wtime} btime {wtime} winc 0 binc 0")
        out, ok = eng.read_until("bestmove", max(120, wtime / 1000 * 3))
        t1 = time.monotonic()
        if not ok:
            continue
        depths = []          # (depth, time) for each completed iteration
        for line in out:
            if line.startswith("info depth"):
                f = line.split()
                d = int(f[f.index("depth") + 1])
                t = float(f[f.index("time") + 1]) if "time" in f else None
                if t is not None:
                    depths.append((d, t))
        last = depths[-1] if depths else (0, None)
        rows.append({"wall": (t1 - t0) * 1000.0, "last_depth": last[0],
                     "last_iter_time": last[1], "n_iter": len(depths)})
    eng.close()
    return rows


def med(v):
    v = [x for x in v if x is not None]
    return statistics.median(v) if v else 0.0


def main() -> int:
    base, pc, outdir = sys.argv[1], sys.argv[2], sys.argv[3]
    npos = int(sys.argv[4]) if len(sys.argv) > 4 else 40
    os.makedirs(outdir, exist_ok=True)
    here = os.path.dirname(os.path.abspath(__file__))
    fens = read_positions([os.path.join(here, "..", "job1", "G.epd"),
                           os.path.join(here, "..", "job1", "O.fens")], npos)
    fens = [f.split(";")[0].split(" bm")[0].strip() for f in fens]

    print("| wtime | plan soft | plan hard | build | n | achieved median | last iteration time | "
          "median last depth | achieved/soft | last-iter/soft |")
    print("|---|---|---|---|---|---|---|---|---|")
    store = {}
    for wtime in CLOCKS:
        soft, hard = plan(wtime)
        for label, exe, pc20 in (("base", base, False), ("PC20", pc, True)):
            rows = cell(exe, fens, wtime, pc20)
            store[(wtime, label)] = rows
            mw = med([r["wall"] for r in rows])
            li = med([r["last_iter_time"] for r in rows])
            md = med([r["last_depth"] for r in rows])
            print(f"| {wtime} | {soft} | {hard} | {label} | {len(rows)} | {mw:.1f} | {li:.0f} | "
                  f"{md:.0f} | {mw/soft:.2f} | {li/soft:.2f} |", flush=True)
            with open(os.path.join(outdir, f"w{wtime}_{label}.tsv"), "w") as fh:
                fh.write("wall_ms\tlast_depth\tlast_iter_time_ms\tn_iterations\n")
                for r in rows:
                    fh.write(f"{r['wall']:.3f}\t{r['last_depth']}\t{r['last_iter_time']}\t"
                             f"{r['n_iter']}\n")
    print()
    print("## The separating comparison (plans are IDENTICAL, so any difference is the stop)")
    print()
    print("| wtime | plan soft | achieved base | achieved PC | PC/base achieved | depth base | "
          "depth PC | last-iter time base | last-iter time PC | reading |")
    print("|---|---|---|---|---|---|---|---|---|---|")
    for wtime in CLOCKS:
        soft, _ = plan(wtime)
        b, p = store[(wtime, "base")], store[(wtime, "PC20")]
        bw, pw = med([r["wall"] for r in b]), med([r["wall"] for r in p])
        bd, pd = med([r["last_depth"] for r in b]), med([r["last_depth"] for r in p])
        bi, pi = med([r["last_iter_time"] for r in b]), med([r["last_iter_time"] for r in p])
        if pd < bd and pw < bw:
            reading = "PC stops earlier AND finishes shallower: the stop cuts the next iteration off"
        elif pd < bd:
            reading = "PC reaches less depth for the same or more time"
        elif pw < bw * 0.95:
            reading = "same depth, less time"
        else:
            reading = "no separation"
        print(f"| {wtime} | {soft} | {bw:.1f} | {pw:.1f} | {pw/bw:.2f} | {bd:.0f} | {pd:.0f} | "
              f"{bi:.0f} | {pi:.0f} | {reading} |")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
