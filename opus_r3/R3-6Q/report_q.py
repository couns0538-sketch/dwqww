#!/usr/bin/env python3
"""R3-6Q: pooled and per-repetition summary of the GitHub runner time-to-depth runs, PC numbers beside.

Uses opus_r3/R3-6/summarize.py unchanged (per-position medians over the repetitions, sums, gmeans,
95% bootstrap intervals over positions). Only positions with all ten (config, threads) cells in a
data set are used for that data set's tables.
usage: report_q.py ttd_rep1.jsonl [ttd_rep2.jsonl ...]
"""
import json
import os
import statistics
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "R3-6"))
import summarize as S  # noqa: E402

CELLS = [("off", 1), ("off", 2), ("off", 3), ("on", 1), ("on", 2), ("on", 3),
         ("offP", 2), ("offP", 3), ("onP", 2), ("onP", 3)]
PAIRS = [("offP", "off"), ("onP", "on"), ("on", "off"), ("onP", "off")]
T1_FROM = {"offP": "off", "onP": "on"}
# R3-6 PC numbers (head 330237f3, loaded PC, 1-2 runs per cell; opus_r3/R3-6/REPORT.md "Results").
PC_MAIN = {  # (config, T): (TTD sum s, per-position speedup gmean, nodes Tn/T1 gmean, NPS scaling, CPUs got)
    ("off", 1): (127.6, 1.00, 1.00, 1.00, 0.81), ("off", 2): (133.6, 1.07, 1.71, 1.86, 1.43),
    ("off", 3): (112.1, 1.24, 2.03, 2.43, 2.04), ("on", 1): (127.9, 1.00, 1.00, 1.00, 0.80),
    ("on", 2): (113.8, 1.28, 1.51, 1.94, 1.48), ("on", 3): (116.3, 1.28, 2.08, 2.72, 2.13),
    ("offP", 2): (131.7, 1.08, 1.83, 1.98, 1.54), ("offP", 3): (120.1, 1.21, 2.18, 2.69, 2.03),
    ("onP", 2): (118.5, 1.21, 1.64, 1.95, 1.51), ("onP", 3): (107.5, 1.40, 2.06, 2.77, 2.19),
}
PC_PAIR = {  # (B, A, T): wall B/A gmean [95% CI] over 30 positions
    ("offP", "off", 2): "0.989 [0.798..1.210]", ("offP", "off", 3): "1.025 [0.862..1.198]",
    ("onP", "on", 2): "1.060 [0.883..1.287]", ("onP", "on", 3): "0.910 [0.691..1.178]",
    ("on", "off", 2): "0.837 [0.665..1.041]", ("on", "off", 3): "0.973 [0.803..1.153]",
    ("onP", "off", 2): "0.888 [0.733..1.072]", ("onP", "off", 3): "0.885 [0.727..1.055]",
}


def complete_positions(table, order):
    return [p for p in order if all((p, c, t) in table for c, t in CELLS)]


def wall_ratio(table, b, a, t, positions):
    ratios = [table[(p, b, t)]["wall"] / table[(p, a, t)]["wall"] for p in positions]
    lo, hi = S.bootstrap_gmean_ci(ratios)
    faster = sum(1 for r in ratios if r < 1)
    return f"{S.gmean(ratios):.3f} [{lo:.3f}..{hi:.3f}]", faster


def section(title, runs):
    table = S.per_position(runs)
    order = []
    for r in runs:
        if r["pos"] not in order:
            order.append(r["pos"])
    pos = complete_positions(table, order)
    print(f"\n## {title}\n")
    reps = sorted({r['rep'] for r in runs})
    print(f"{len(runs)} runs, repetitions {reps}, {len(pos)}/{len(order)} positions complete")
    if not pos:
        return None, []
    print()
    print(S.fmt(S.summarise(table, ["off", "on", "offP", "onP"], [1, 2, 3], pos, T1_FROM)))
    print("\nPaired comparisons (per-position medians; ratio < 1 = B needs less; 95% bootstrap CI over positions)\n")
    print(S.paired(table, PAIRS, [1, 2, 3], pos))
    return table, pos


def main():
    runs = []
    for path in sys.argv[1:]:
        runs.extend(json.loads(l) for l in open(path, encoding="utf-8") if l.strip())
    if not runs:
        print("no runs")
        return 1
    offs = sorted({r.get("depth_offset", 0) for r in runs})
    nprocs = sorted({r.get("nproc") for r in runs})
    print("# R3-6Q: Lazy SMP time-to-depth on GitHub ubuntu-24.04 runners")
    print(f"\ndepth offset(s): {offs} (search depth = R3-6 position depth - offset); nproc: {nprocs}")
    for cfg, t in CELLS:
        rs = [r for r in runs if r["config"] == cfg and r["threads"] == t]
        if rs:
            st = [r["steal_frac"] for r in rs if r.get("steal_frac") is not None]
            ob = [r["other_busy"] for r in rs if r.get("other_busy") is not None]
            print(f"- {cfg} T{t}: {len(rs)} runs, CPUs got median {statistics.median(r['cpu_s'] / r['wall_s'] for r in rs):.2f}, "
                  f"other load median {statistics.median(ob) if ob else float('nan'):.3f}, "
                  f"steal median {statistics.median(st) if st else float('nan'):.4f} max {max(st) if st else float('nan'):.4f}")
    t1 = {}
    for r in runs:
        if r["threads"] == 1:
            t1.setdefault((r["pos"], r["config"]), set()).add(r["nodes"])
    same = sum(1 for v in t1.values() if len(v) == 1)
    print(f"- Threads=1 determinism: {same}/{len(t1)} (position, config) cells have identical nodes in every repetition")
    table, pos = section("Pooled over the repetitions (per-position medians)", runs)
    by_rep = {}
    for r in runs:
        by_rep.setdefault(r["rep"], []).append(r)
    rep_tables = {}
    for rep in sorted(by_rep):
        rep_tables[rep] = section(f"Repetition {rep + 1}", by_rep[rep])
    if not table:
        return 0
    print("\n## GitHub runners vs the loaded PC (R3-6)\n")
    print("| config | T | GH TTD sum s | PC TTD sum s | GH speedup gmean | PC | GH nodes Tn/T1 | PC | GH NPS scaling | PC "
          "| GH CPUs got | PC |")
    print("|" + "---|" * 12)
    lines = {(l["config"], l["threads"]): l for l in S.summarise(table, ["off", "on", "offP", "onP"], [1, 2, 3], pos, T1_FROM)}
    for cell in CELLS:
        l = lines.get(cell)
        pc = PC_MAIN[cell]
        if not l:
            continue
        g = lambda k: f"{l[k]:.2f}" if k in l else "-"  # noqa: E731
        print(f"| {cell[0]} | {cell[1]} | {l['ttd_sum']:.1f} | {pc[0]:.1f} | {g('sp_gmean')} | {pc[1]:.2f} | "
              f"{g('nodes_ratio')} | {pc[2]:.2f} | {g('nps_scaling')} | {pc[3]:.2f} | {l['par']:.2f} | {pc[4]:.2f} |")
    print("\n| B vs A | T | GH pooled wall B/A [95% CI] | B faster | " +
          " | ".join(f"GH rep {rep + 1}" for rep in sorted(rep_tables)) + " | PC (R3-6) wall B/A [95% CI] |")
    print("|" + "---|" * (5 + len(rep_tables)))
    for b, a in PAIRS:
        for t in (2, 3):
            pooled, faster = wall_ratio(table, b, a, t, pos)
            cells = []
            for rep in sorted(rep_tables):
                rt, rp = rep_tables[rep]
                cells.append(wall_ratio(rt, b, a, t, rp)[0] if rt and rp else "-")
            print(f"| {b} vs {a} | {t} | {pooled} | {faster}/{len(pos)} | " + " | ".join(cells) +
                  f" | {PC_PAIR[(b, a, t)]} |")
    return 0


if __name__ == "__main__":
    sys.exit(main())
