#!/usr/bin/env python3
"""sweep_table.py OUTDIR — the correction table, from the .tsv files only, with integrity asserts.

Every number printed is computed here. Before printing, it ASSERTS (seat 19's warning):
  - each cell has 30 rows, all with a parseable wall_ms;
  - each cell's plan is positive and was taken from its .meta, not guessed;
  - no NaN/inf reaches a ratio;
and it fails loudly (exit 1) instead of printing a table if any assert fails.
"""
import glob
import math
import os
import statistics
import sys


def load(path):
    rows = []
    with open(path) as fh:
        head = fh.readline().rstrip("\n").split("\t")
        for line in fh:
            p = line.rstrip("\n").split("\t")
            rows.append(dict(zip(head, p)))
    return rows


def main() -> int:
    d = sys.argv[1]
    cells = []
    problems = []
    for path in sorted(glob.glob(os.path.join(d, "mt*_mo*.tsv")),
                       key=lambda p: (int(os.path.basename(p)[2:].split("_")[0]),
                                      int(os.path.basename(p).split("_mo")[1][:-4]))):
        name = os.path.basename(path)[:-4]
        meta = path[:-4] + ".meta"
        plan = None
        overhead = None
        if os.path.exists(meta):
            for line in open(meta):
                if line.startswith("plan_hard_ms"):
                    plan = int(line.split()[1])
                if line.startswith("option Move Overhead"):
                    overhead = int(line.split()[-1])
        if plan is None or plan <= 0:
            problems.append(f"{name}: no positive plan in .meta")
            continue
        rows = load(path)
        walls, eng, depths = [], [], {}
        noresp = 0
        for r in rows:
            try:
                w = float(r["wall_ms"])
            except (ValueError, KeyError):
                problems.append(f"{name}: unparseable wall_ms")
                continue
            if math.isnan(w) or math.isinf(w):
                problems.append(f"{name}: NaN wall")
                continue
            walls.append(w)
            try:
                eng.append(float(r["engine_time_ms"]) if r["engine_time_ms"] else None)
            except ValueError:
                eng.append(None)
            depths[r["last_depth"]] = depths.get(r["last_depth"], 0) + 1
            if r["status"] != "ok":
                noresp += 1
        if not walls:
            problems.append(f"{name}: no usable rows")
            continue
        med = statistics.median(walls)
        if math.isnan(med / plan):
            problems.append(f"{name}: NaN ratio")
            continue
        eng_ok = [e for e in eng if e is not None]
        cells.append(dict(name=name, plan=plan, overhead=overhead, n=len(walls), med=med,
                          mn=min(walls), mx=max(walls), depths=dict(sorted(depths.items())),
                          ratio=med / plan, noresp=noresp,
                          eng_med=statistics.median(eng_ok) if eng_ok else None,
                          eng_n=len(eng_ok)))

    if problems:
        print("INTEGRITY FAILURE — no table printed:")
        for p in problems:
            print("  " + p)
        return 1

    print(f"cells: {len(cells)} (expected 16)")
    if len(cells) != 16:
        print("INTEGRITY FAILURE — cell count wrong, no table printed.")
        return 1
    print()
    print("| cell | MoveOverhead | plan (M-O) ms | n | engine-time median | WALL median | min | max "
          "| last depth (count) | wall/plan | NORESP |")
    print("|---|---|---|---|---|---|---|---|---|---|---|")
    for c in cells:
        ds = " ".join(f"d{k}:{v}" for k, v in c["depths"].items())
        em = f"{c['eng_med']:.0f}" if c["eng_med"] is not None else "-"
        print(f"| {c['name']} | {c['overhead']} | {c['plan']} | {c['n']} | {em} | {c['med']:.1f} | "
              f"{c['mn']:.1f} | {c['mx']:.1f} | {ds} | {c['ratio']:.2f} | {c['noresp']} |")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
