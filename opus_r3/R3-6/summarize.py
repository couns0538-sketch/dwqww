#!/usr/bin/env python3
"""R3-6: summarise smp_ttd.py runs.

Per (position, config, threads): median over the repetitions of wall time-to-depth, process CPU
time, nodes (first `info depth D` line), NPS (nodes / wall) and CPU-NPS (nodes / CPU time), plus
min/max, effective parallelism (CPU / wall) and the median "other" load.
Per (config, threads), over the positions:
  ttd_sum      sum of the per-position median wall times (the suite's time-to-depth)
  speedup      ttd_sum(T1) / ttd_sum(Tn) of the same config
  sp_gmean     geometric mean of the per-position speedups (median T1 / median Tn), with the
               25th..75th percentile of the per-position speedups as spread
  nodes_ratio  geometric mean of per-position node inflation (median nodes Tn / median nodes T1)
  nps          total nodes / total wall; nps_scaling = nps / nps(T1)
  cpu_ratio    geometric mean of CPU time Tn / CPU time T1 (total work done for the same depth)
  cpu_speedup  n / cpu_ratio: the speedup if all n threads had run without interruption the whole
               time (load-free estimate; it overstates the speedup when helpers sit idle)
  cpu_nps_thr  nodes per CPU second (per-thread speed) relative to T1
  par          median CPU / wall: how many CPUs the engine actually got (n = no starvation)
  other        median busy fraction of the rest of the PC during the runs
Paired comparison (--pair B:A): per thread count, the geometric mean over positions of the
per-position median ratios B/A of wall time, CPU time and nodes, with a 95% bootstrap interval
(positions resampled), and how many positions B finished faster.
usage: summarize.py runs.jsonl [more.jsonl ...] [--tsv per_position.tsv] [--by-class]
       [--configs A,B] [--t1-from offP=off ...] [--pair offP:off ...]
"""
import argparse
import json
import math
import statistics
from collections import defaultdict


def gmean(xs):
    xs = [x for x in xs if x and x > 0]
    return math.exp(sum(math.log(x) for x in xs) / len(xs)) if xs else float("nan")


def pct(xs, q):
    xs = sorted(xs)
    if not xs:
        return float("nan")
    k = (len(xs) - 1) * q
    f = math.floor(k)
    c = min(f + 1, len(xs) - 1)
    return xs[f] + (xs[c] - xs[f]) * (k - f)


def load(paths):
    runs = []
    for p in paths:
        for line in open(p, encoding="utf-8"):
            runs.append(json.loads(line))
    return runs


def per_position(runs):
    groups = defaultdict(list)
    for r in runs:
        groups[(r["pos"], r["config"], r["threads"])].append(r)
    table = {}
    for key, rs in groups.items():
        walls = [r["wall_s"] for r in rs]
        cpus = [r["cpu_s"] for r in rs]
        nodes = [r["nodes"] for r in rs]
        table[key] = {
            "pos": key[0], "class": rs[0]["class"], "depth": rs[0]["depth"], "config": key[1], "threads": key[2],
            "n": len(rs), "wall": statistics.median(walls), "wall_min": min(walls), "wall_max": max(walls),
            "cpu": statistics.median(cpus), "nodes": statistics.median(nodes), "nodes_min": min(nodes),
            "nodes_max": max(nodes), "nps": statistics.median(n / w for n, w in zip(nodes, walls)),
            "cpu_nps": statistics.median(n / c for n, c in zip(nodes, cpus) if c > 0),
            "par": statistics.median(c / w for c, w in zip(cpus, walls)),
            "other": statistics.median(r["other_busy"] for r in rs if r["other_busy"] is not None),
            "hashfull": statistics.median(r["hashfull"] for r in rs),
            "moves": ",".join(sorted({r["bestmove"] for r in rs})),
            "scores": ",".join(str(r["score"]) for r in rs),
        }
    return table


def summarise(table, configs, threads, positions, t1_from=None, label=""):
    out = []
    for cfg in configs:
        ref_cfg = (t1_from or {}).get(cfg, cfg)
        base = {p: table.get((p, ref_cfg, 1)) for p in positions}
        if any(v is None for v in base.values()):
            base = None
        for t in threads:
            rows = [table.get((p, cfg, t)) for p in positions]
            if any(r is None for r in rows):
                continue
            ttd = sum(r["wall"] for r in rows)
            nodes = sum(r["nodes"] for r in rows)
            line = {"config": cfg, "threads": t, "positions": len(rows), "ttd_sum": ttd, "nodes_sum": nodes,
                    "nps": nodes / ttd, "par": statistics.median(r["par"] for r in rows),
                    "other": statistics.median(r["other"] for r in rows), "label": label,
                    "hashfull": statistics.median(r["hashfull"] for r in rows),
                    "wall_spread": statistics.median((r["wall_max"] - r["wall_min"]) / r["wall"] for r in rows)}
            if base:
                b = [base[p] for p in positions]
                sp = [bb["wall"] / r["wall"] for bb, r in zip(b, rows)]
                line.update({
                    "speedup": sum(bb["wall"] for bb in b) / ttd,
                    "sp_gmean": gmean(sp), "sp_p25": pct(sp, 0.25), "sp_p75": pct(sp, 0.75),
                    "nodes_ratio": gmean([r["nodes"] / bb["nodes"] for bb, r in zip(b, rows)]),
                    "nr_p25": pct([r["nodes"] / bb["nodes"] for bb, r in zip(b, rows)], 0.25),
                    "nr_p75": pct([r["nodes"] / bb["nodes"] for bb, r in zip(b, rows)], 0.75),
                    "nps_scaling": (nodes / ttd) / (sum(bb["nodes"] for bb in b) / sum(bb["wall"] for bb in b)),
                    "cpu_ratio": gmean([r["cpu"] / bb["cpu"] for bb, r in zip(b, rows)]),
                    "cpu_nps_thr": gmean([r["cpu_nps"] / bb["cpu_nps"] for bb, r in zip(b, rows)]),
                })
                line["cpu_speedup"] = t / line["cpu_ratio"]
            out.append(line)
    return out


def fmt(lines):
    hdr = ("| config | T | pos | TTD sum s | speedup | per-pos speedup gmean [p25..p75] | nodes Tn/T1 gmean "
           "[p25..p75] | NPS | NPS scaling | CPU Tn/T1 | load-free speedup | CPU-NPS/thread | CPUs got | other load "
           "| wall spread | hashfull |")
    rows = [hdr, "|" + "---|" * 17]
    for l in lines:
        g = lambda k, f="{:.2f}": f.format(l[k]) if k in l and l[k] == l[k] else "-"  # noqa: E731
        rows.append(f"| {l['config']}{l['label']} | {l['threads']} | {l['positions']} | {l['ttd_sum']:.1f} | "
                    f"{g('speedup')} | {g('sp_gmean')} [{g('sp_p25')}..{g('sp_p75')}] | "
                    f"{g('nodes_ratio')} [{g('nr_p25')}..{g('nr_p75')}] | {l['nps'] / 1e6:.3f} M | "
                    f"{g('nps_scaling')} | {g('cpu_ratio')} | {g('cpu_speedup')} | {g('cpu_nps_thr')} | "
                    f"{l['par']:.2f} | {l['other']:.2f} | {l['wall_spread'] * 100:.0f}% | {l['hashfull']:.0f} |")
    return "\n".join(rows)


def bootstrap_gmean_ci(xs, iters=4000, seed=6):
    """95% percentile bootstrap interval of the geometric mean of xs (resampling positions)."""
    import random
    rng = random.Random(seed)
    logs = [math.log(x) for x in xs]
    means = []
    for _ in range(iters):
        sample = [logs[rng.randrange(len(logs))] for _ in logs]
        means.append(sum(sample) / len(sample))
    means.sort()
    return math.exp(means[int(0.025 * iters)]), math.exp(means[int(0.975 * iters) - 1])


def paired(table, pairs, threads, positions):
    """B vs A per thread count: geometric means over positions of the per-position median ratios."""
    rows = ["| B vs A | T | pos | wall B/A gmean [95% CI] | CPU B/A gmean [95% CI] | nodes B/A gmean [95% CI] | "
            "positions with B faster | TTD sum A s | TTD sum B s |", "|" + "---|" * 9]
    for b_cfg, a_cfg in pairs:
        for t in threads:
            ab = [(table.get((p, a_cfg, t)), table.get((p, b_cfg, t))) for p in positions]
            if any(x is None or y is None for x, y in ab):
                continue
            cells = []
            for key in ("wall", "cpu", "nodes"):
                ratios = [y[key] / x[key] for x, y in ab]
                lo, hi = bootstrap_gmean_ci(ratios)
                cells.append(f"{gmean(ratios):.3f} [{lo:.3f}..{hi:.3f}]")
            faster = sum(1 for x, y in ab if y["wall"] < x["wall"])
            rows.append(f"| {b_cfg} vs {a_cfg} | {t} | {len(ab)} | {cells[0]} | {cells[1]} | {cells[2]} | "
                        f"{faster}/{len(ab)} | {sum(x['wall'] for x, _ in ab):.1f} | {sum(y['wall'] for _, y in ab):.1f} |")
    return "\n".join(rows)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("runs", nargs="+")
    ap.add_argument("--tsv")
    ap.add_argument("--by-class", action="store_true")
    ap.add_argument("--configs", default="")
    ap.add_argument("--t1-from", action="append", default=[],
                    help="CFG=REF: Threads=1 reference of a config that has no Threads=1 runs")
    ap.add_argument("--pair", action="append", default=[], help="B:A paired comparison of two configs")
    a = ap.parse_args()
    t1_from = dict(item.split("=", 1) for item in a.t1_from)
    runs = load(a.runs)
    table = per_position(runs)
    configs = a.configs.split(",") if a.configs else sorted({r["config"] for r in runs}, key=lambda c: (len(c), c))
    threads = sorted({r["threads"] for r in runs})
    order = []
    for r in runs:
        if r["pos"] not in order:
            order.append(r["pos"])
    print(f"{len(runs)} runs, {len(order)} positions, configs {configs}, threads {threads}")
    reps = defaultdict(int)
    for r in runs:
        reps[(r["config"], r["threads"])] += 1
    print("runs per (config, threads):", dict(reps))
    print()
    print(fmt(summarise(table, configs, threads, order, t1_from)))
    if a.pair:
        print("\npaired comparisons (per-position medians; ratio < 1 = B needs less)")
        print(paired(table, [tuple(p.split(":", 1)) for p in a.pair], threads, order))
    if a.by_class:
        for cls in ("opening", "middlegame", "endgame"):
            ps = [p for p in order if table[(p, configs[0], threads[0])]["class"] == cls]
            print(f"\n{cls} ({len(ps)} positions)")
            print(fmt(summarise(table, configs, threads, ps, t1_from)))
            if a.pair:
                print(paired(table, [tuple(p.split(":", 1)) for p in a.pair], threads, ps))
    if a.tsv:
        keys = ["pos", "class", "depth", "config", "threads", "n", "wall", "wall_min", "wall_max", "cpu", "nodes",
                "nodes_min", "nodes_max", "nps", "cpu_nps", "par", "other", "hashfull", "moves", "scores"]
        with open(a.tsv, "w", encoding="utf-8", newline="\n") as fh:
            fh.write("\t".join(keys) + "\n")
            for p in order:
                for c in configs:
                    for t in threads:
                        r = table.get((p, c, t))
                        if r:
                            fh.write("\t".join(f"{r[k]:.4f}" if isinstance(r[k], float) else str(r[k])
                                               for k in keys) + "\n")
        print(f"\nper-position TSV: {a.tsv}")


if __name__ == "__main__":
    main()
