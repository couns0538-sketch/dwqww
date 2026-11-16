#!/usr/bin/env python3
"""clock_with_plan.py OUTDIR — re-read the EXISTING job2/job3 raw files against the ENGINE'S plans.

No new measurement is needed for the plan columns: the raw files already hold, per search, the wall
time, the engine's own reported time, the last completed depth and the status. What was missing from my
job 2 and job 3 reports is the engine's PLAN beside them, and the last completed depth, which is the
quantity seat 16 says dominates.

For each cell this prints:
  plan soft / plan hard   — recomputed from include/forge/clock_plan.hpp with the source defaults
                            (TmSoftDivisor 22, TmIncrementPercent 75, TmHardPercent 60,
                             TmHardSoftMultiple 5, MoveOverhead 10)
  achieved median         — the WALL time (the stop)
  last-info median        — the engine's reported `time` (last completed iteration)
  last depth (mode)       — the depth the search actually finished
and counts, per cell, searches over the engine's soft plan and over its hard plan.

Asserts: every row's wall time parses; no ratio is formed against a zero plan.
"""
import glob
import math
import os
import statistics
import sys

OVERHEAD = 10
SOFT_DIV = 22
INC_PCT = 75
HARD_PCT = 60
HARD_MULT = 5


def plan(time_ms, inc_ms, mtg=0):
    if time_ms <= OVERHEAD:
        return 0, 0
    avail = time_ms - OVERHEAD
    if mtg > 0:
        m = min(mtg, 50)
        soft = avail // (m + 1) + inc_ms * 3 // 4
        hard = min(avail * 4 // 5, soft * 4)
    else:
        soft = avail // SOFT_DIV + inc_ms * INC_PCT // 100
        hard = min(avail * HARD_PCT // 100, soft * HARD_MULT)
    soft = max(1, min(soft, avail))
    hard = max(1, min(hard, avail))
    if soft > hard:
        soft = hard
    return soft, hard


def read_tsv(path):
    rows = []
    with open(path) as fh:
        head = fh.readline().rstrip("\n").split("\t")
        for line in fh:
            p = line.rstrip("\n").split("\t")
            rows.append(dict(zip(head, p)))
    return rows


def summarise(path, soft, hard, label):
    rows = read_tsv(path)
    walls, eng, depths = [], [], {}
    bad = 0
    for r in rows:
        try:
            w = float(r["wall_ms"])
        except (ValueError, KeyError):
            bad += 1
            continue
        if math.isnan(w) or math.isinf(w):
            bad += 1
            continue
        walls.append(w)
        try:
            eng.append(float(r["engine_time_ms"]) if r.get("engine_time_ms") else None)
        except ValueError:
            eng.append(None)
        d = r.get("last_depth")
        if d:
            depths[d] = depths.get(d, 0) + 1
    eng_ok = [e for e in eng if e is not None]
    if not walls or soft <= 0:
        return None
    mode = max(depths, key=depths.get) if depths else "-"
    return dict(label=label, n=len(walls), bad=bad, soft=soft, hard=hard,
                med=statistics.median(walls),
                eng_med=statistics.median(eng_ok) if eng_ok else None,
                over_soft=sum(1 for w in walls if w > soft),
                over_hard=sum(1 for w in walls if w > hard),
                mode=mode, depths=depths)


def main() -> int:
    root = sys.argv[1]
    out = []
    # job 2: wTIME_iWINC
    for path in sorted(glob.glob(os.path.join(root, "job2/out/w*_i*.tsv"))):
        base = os.path.basename(path)[:-4]
        wtime = int(base.split("_")[0][1:])
        winc = int(base.split("_")[1][1:])
        soft, hard = plan(wtime, winc)
        r = summarise(path, soft, hard, base)
        if r:
            out.append(r)
    # job 3: mtgN
    for path in sorted(glob.glob(os.path.join(root, "job3/out/mtg*.tsv"))):
        mtg = int(os.path.basename(path)[3:-4])
        soft, hard = plan(1000, 0, mtg)
        r = summarise(path, soft, hard, f"mtg{mtg}")
        if r:
            out.append(r)

    print("| cell | n | plan soft | plan hard | achieved (wall) median | last-info median | "
          "last depth (mode) | over SOFT | over HARD |")
    print("|---|---|---|---|---|---|---|---|---|")
    for r in out:
        em = f"{r['eng_med']:.0f}" if r["eng_med"] is not None else "-"
        print(f"| {r['label']} | {r['n']} | {r['soft']} | {r['hard']} | {r['med']:.1f} | {em} | "
              f"d{r['mode']} | {r['over_soft']} | {r['over_hard']} |")
    bad = sum(r["bad"] for r in out)
    print()
    print(f"cells: {len(out)}; unparseable wall rows: {bad}")
    if bad:
        print("INTEGRITY FAILURE — some rows had no usable timestamp; table above is incomplete.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
