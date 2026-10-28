#!/usr/bin/env python3
"""R3-6Q: runner speed check -> one uniform depth offset (0, 1 or 2 plies) for every repetition.

Input: Threads=1 `off` runs of a sample of the 30 positions at their full depth on the runner
(smp_ttd_linux.py output) and the PC's per-position medians (R3-6 logs/ttd_per_position.tsv).
  speed ratio r = sum(runner T1 wall) / sum(PC T1 wall) over the sampled positions
  job estimate  = r * PC_JOB_S + RUNS * OVERHEAD_S, where PC_JOB_S = 1209 s is the sum of the R3-6 PC
                  time-to-depth sums of the ten (config, threads) cells one job runs (off/on T1-3,
                  offP/onP T2-3). The PC's T2/T3 runs were starved by load, so this overestimates a
                  quiet runner.
  offset k      : the estimate scaled by the runner's own time-to-(D-k) / time-to-D (first `info depth`
                  lines of the sampled runs); the smallest k in 0..2 whose estimate is <= LIMIT_S.
Prints a markdown report and a final line `depth_offset=K`.
usage: choose_depth.py <runner_t1.jsonl> <pc ttd_per_position.tsv> [--limit-s 2520]
"""
import argparse
import json

PC_JOB_S = 127.6 + 133.6 + 112.1 + 127.9 + 113.8 + 116.3 + 131.7 + 120.1 + 118.5 + 107.5
RUNS = 300
OVERHEAD_S = 0.3


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("runner")
    ap.add_argument("pc_tsv")
    ap.add_argument("--limit-s", type=float, default=2520)
    a = ap.parse_args()
    runs = [json.loads(l) for l in open(a.runner, encoding="utf-8") if l.strip()]
    pc = {}
    lines = open(a.pc_tsv, encoding="utf-8").read().splitlines()
    keys = lines[0].split("\t")
    for line in lines[1:]:
        row = dict(zip(keys, line.split("\t")))
        if row["config"] == "off" and row["threads"] == "1":
            pc[row["pos"]] = (float(row["wall"]), float(row["nodes"]))
    print("| position | depth | runner T1 wall s | PC T1 wall s | ratio | runner nodes | PC nodes |")
    print("|---|---|---|---|---|---|---|")
    rw = pw = 0.0
    frac = {0: 0.0, 1: 0.0, 2: 0.0}
    for r in runs:
        p_wall, p_nodes = pc[r["pos"]]
        rw += r["wall_s"]
        pw += p_wall
        times = {d: ms for d, ms, _ in r["iters"]}
        for k in frac:
            frac[k] += times.get(r["depth"] - k, 0) / 1000.0
        print(f"| {r['pos']} | {r['depth']} | {r['wall_s']:.2f} | {p_wall:.2f} | {r['wall_s'] / p_wall:.2f} | "
              f"{r['nodes']} | {p_nodes:.0f} |")
    ratio = rw / pw
    base = ratio * PC_JOB_S + RUNS * OVERHEAD_S
    print(f"\nspeed ratio runner/PC (T1 wall, {len(runs)} positions): {ratio:.3f}")
    print(f"PC per-job sum of time-to-depth sums: {PC_JOB_S:.1f} s; limit {a.limit_s:.0f} s")
    choice = 2
    for k in (0, 1, 2):
        est = base * (frac[k] / frac[0] if frac[0] > 0 else 1.0)
        print(f"offset {k}: time-to-(D-{k}) / time-to-D = {frac[k] / frac[0]:.3f}, job estimate {est:.0f} s")
        if est <= a.limit_s and choice == 2 and k < 2:
            choice = k
            break
    print(f"\ndepth_offset={choice}")


if __name__ == "__main__":
    main()
